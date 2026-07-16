#!/usr/bin/env python3
from __future__ import annotations

import argparse
import asyncio
import importlib
import json
import os
from pathlib import Path
import sys
import time
from typing import Any, Callable

from _lib.google_api import (
    HTTPStatusError,
    ScriptError,
    capture_json,
    reset_connection,
    reset_json_capture,
    select_connection,
)

OPS = {
    "gmail": "gmail_ops",
    "google-calendar": "calendar_ops",
    "google-drive": "drive_ops",
    "google-docs": "docs_ops",
    "google-sheets": "sheets_ops",
    "google-slides": "slides_ops",
    "linear": "linear_ops",
    "notion": "notion_ops",
    "ramp": "ramp_ops",
    "slack": "slack_ops",
}

PROVIDERS = {
    "gmail": "google",
    "google-calendar": "google",
    "google-drive": "google",
    "google-docs": "google",
    "google-sheets": "google",
    "google-slides": "google",
    "linear": "linear",
    "notion": "notion",
    "ramp": "ramp",
    "slack": "slack",
}

# These account-wide discovery operations intentionally run once per active
# connection and always return the multi-connection envelope, even with one match.
DISCOVERY_OPERATIONS = {
    "gmail": {"list_labels", "search_messages"},
    "google-calendar": {"find_next_upcoming_event", "list_calendars"},
    "google-drive": {"list_shared_drives", "search_files"},
    "google-docs": {"find_documents"},
    "google-sheets": {"find_spreadsheets"},
    "google-slides": {"find_presentations"},
    "linear": {"list_labels", "list_teams", "list_users", "list_workflow_states", "search_issues"},
    "notion": {"search"},
    "ramp": {"list_funds", "list_reimbursements", "list_users", "list_virtual_cards"},
    "slack": {"find_conversation", "list_conversations", "list_users", "search_messages"},
}

# Pure string parsing helpers neither consume nor select a connection.
LOCAL_OPERATIONS = {
    "google-docs": {"extract_document_id"},
    "google-slides": {"extract_presentation_id"},
}

Connection = dict[str, Any]


def run(script_path: Path) -> None:
    service = script_path.parent.name
    operation = script_path.stem.replace("-", "_")
    module_name = OPS.get(service)
    if module_name is None:
        raise SystemExit(f"Unknown script service directory: {service}")
    module = importlib.import_module(f"_lib.{module_name}")
    handler = getattr(module, operation, None)
    if handler is None:
        raise SystemExit(f"No Python handler for {service}/{script_path.name}")
    try:
        connection_id = _parse_connection_id(script_path)
        if operation in LOCAL_OPERATIONS.get(service, set()):
            if connection_id is not None:
                raise ScriptError(
                    f"{service}/{script_path.name} is a local operation and does not accept "
                    "--buoy-connection-id."
                )
            _print_result(_invoke(handler, None))
            return

        connections = _provider_connections(PROVIDERS[service])
        if operation in DISCOVERY_OPERATIONS.get(service, set()):
            if connection_id is not None:
                raise ScriptError(
                    f"{service}/{script_path.name} searches every active {PROVIDERS[service]} "
                    "connection and does not accept --buoy-connection-id."
                )
            results = asyncio.run(_run_discovery(handler, connections))
            print(json.dumps(results, indent=2, ensure_ascii=False))
            return

        connection = _select_target_connection(
            service, script_path.name, PROVIDERS[service], connections, connection_id
        )
        _print_result(_invoke(handler, connection))
    except ScriptError as exc:
        print(str(exc), file=sys.stderr)
        raise SystemExit(1) from None


def _parse_connection_id(script_path: Path) -> str | None:
    parser = argparse.ArgumentParser(prog=str(script_path))
    parser.add_argument(
        "--buoy-connection-id",
        help=(
            "active connection ID to use for a targeted read, account operation, download, "
            "continuation, or mutation"
        ),
    )
    return parser.parse_args().buoy_connection_id


def _select_target_connection(
    service: str,
    script_name: str,
    provider: str,
    connections: list[Connection],
    connection_id: str | None,
) -> Connection:
    if connection_id is not None:
        connection = next(
            (
                candidate
                for candidate in connections
                if candidate["connectionID"] == connection_id
            ),
            None,
        )
        if connection is None:
            raise ScriptError(
                f"{connection_id} is not an active {provider} connection for "
                f"{service}/{script_name}."
            )
        return connection

    if len(connections) == 1:
        return connections[0]

    choices = ", ".join(connection["connectionID"] for connection in connections)
    raise ScriptError(
        f"{service}/{script_name} found {len(connections)} active {provider} connections. "
        "Pass --buoy-connection-id with the connection that owns the target entity or "
        f"mutation. Active choices: {choices}."
    )


def _load_connections() -> list[Connection]:
    raw = os.environ.get("BUOY_CONNECTIONS")
    if raw is None or raw == "":
        raise ScriptError(
            "BUOY_CONNECTIONS is not set. Call set_active_connections before running connector scripts."
        )
    try:
        value = json.loads(raw)
    except json.JSONDecodeError as exc:
        raise ScriptError(f"BUOY_CONNECTIONS must be valid JSON: {exc}") from None
    if not isinstance(value, list):
        raise ScriptError("BUOY_CONNECTIONS must be a JSON array.")

    connections: list[Connection] = []
    required = {"connectionID": str, "provider": str, "accessToken": str}
    for index, connection in enumerate(value):
        if not isinstance(connection, dict):
            raise ScriptError(f"BUOY_CONNECTIONS[{index}] must be an object.")
        for field, field_type in required.items():
            if not isinstance(connection.get(field), field_type) or connection[field] == "":
                raise ScriptError(f"BUOY_CONNECTIONS[{index}].{field} must be a non-empty string.")
        if not isinstance(connection.get("friendlyID"), str):
            raise ScriptError(f"BUOY_CONNECTIONS[{index}].friendlyID must be a string.")
        expires_at = connection.get("expiresAt")
        if not isinstance(expires_at, (int, float)) or isinstance(expires_at, bool):
            raise ScriptError(f"BUOY_CONNECTIONS[{index}].expiresAt must be Unix milliseconds.")
        connections.append(connection)
    return connections


def _provider_connections(provider: str) -> list[Connection]:
    connections = [connection for connection in _load_connections() if connection["provider"] == provider]
    if not connections:
        raise ScriptError(
            f"No active {provider} connection. Call set_active_connections with at least one {provider} connection."
        )
    return connections


def _invoke(handler: Callable[[], None], connection: Connection | None) -> Any:
    connection_token = select_connection(connection) if connection is not None else None
    capture_token, captured = capture_json()
    try:
        if connection is not None and connection["expiresAt"] <= time.time() * 1000:
            raise ScriptError(
                f"The active token for connection {connection['connectionID']} has expired. "
                "Call set_active_connections again before retrying."
            )
        handler()
        if len(captured) != 1:
            raise ScriptError(f"Script produced {len(captured)} JSON values; expected exactly one.")
        return captured[0]
    finally:
        reset_json_capture(capture_token)
        if connection_token is not None:
            reset_connection(connection_token)


async def _run_discovery(
    handler: Callable[[], None], connections: list[Connection]
) -> list[dict[str, Any]]:
    async def invoke(connection: Connection) -> dict[str, Any]:
        try:
            data = await asyncio.to_thread(_invoke, handler, connection)
            return {"$connectionID": connection["connectionID"], "$ok": True, "$data": data}
        except BaseException as exc:
            return {
                "$connectionID": connection["connectionID"],
                "$ok": False,
                "$data": _error_data(exc),
            }

    return list(await asyncio.gather(*(invoke(connection) for connection in connections)))


def _error_data(exc: BaseException) -> Any:
    if isinstance(exc, HTTPStatusError):
        try:
            body: Any = json.loads(exc.text)
        except json.JSONDecodeError:
            body = exc.text
        return {"status": exc.status, "error": body}
    message = str(exc)
    return message if message else exc.__class__.__name__


def _print_result(result: Any) -> None:
    print(json.dumps(result, indent=2, ensure_ascii=False))
