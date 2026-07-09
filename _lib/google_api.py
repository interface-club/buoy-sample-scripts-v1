#!/usr/bin/env python3
from __future__ import annotations

import base64
import csv
import json
import mimetypes
import os
import re
import sys
import time
import urllib.error
import urllib.parse
import urllib.request
from collections.abc import Iterable, Mapping
from datetime import date, datetime, time as dtime, timedelta, timezone
from email.message import EmailMessage
from pathlib import Path
from typing import Any

try:
    from zoneinfo import ZoneInfo
except Exception:  # pragma: no cover
    ZoneInfo = None


class ScriptError(Exception):
    pass


class HTTPStatusError(Exception):
    def __init__(self, status: int, body: bytes, headers: Any):
        self.status = status
        self.body = body
        self.headers = headers
        super().__init__(f"HTTP {status}")

    @property
    def text(self) -> str:
        return self.body.decode("utf-8", errors="replace")


def fail(message: str, code: int = 1) -> None:
    print(message, file=sys.stderr)
    raise SystemExit(code)


def env(name: str, default: str | None = None, *, required: bool = False) -> str:
    value = os.environ.get(name)
    if value is None or value == "":
        if required and default is None:
            fail(f"{name} is required")
        return "" if default is None else default
    return value


def env_int(name: str, default: int) -> int:
    raw = env(name, str(default))
    try:
        return int(raw)
    except ValueError:
        fail(f"{name} must be an integer")


def env_bool(name: str, default: bool) -> bool:
    raw = env(name, "true" if default else "false").strip().lower()
    return raw not in {"0", "false", "no", "off", ""}


def env_json(name: str, default: Any = None, *, required: bool = False) -> Any:
    raw = os.environ.get(name)
    if raw is None or raw == "":
        if required:
            fail(f"{name} is required")
        return default
    try:
        return json.loads(raw)
    except json.JSONDecodeError as exc:
        fail(f"{name} must be valid JSON: {exc}")


def access_token() -> str:
    return env("ACCESS_TOKEN", required=True)


def url_quote(value: str) -> str:
    return urllib.parse.quote(value, safe="")


QueryParams = Mapping[str, Any] | Iterable[tuple[str, Any]]


def query_value(value: Any) -> Any:
    if isinstance(value, bool):
        return "true" if value else "false"
    return value


def build_url(url: str, params: QueryParams | None = None) -> str:
    if not params:
        return url
    clean: list[tuple[str, Any]] = []
    items = params.items() if isinstance(params, Mapping) else params
    for key, value in items:
        if value is None:
            continue
        if isinstance(value, (list, tuple)):
            clean.extend((key, query_value(item)) for item in value if item is not None)
        else:
            clean.append((key, query_value(value)))
    query = urllib.parse.urlencode(clean, doseq=True)
    sep = "&" if "?" in url else "?"
    return url + (sep + query if query else "")


def request(
    method: str,
    url: str,
    *,
    token: str | None = None,
    params: QueryParams | None = None,
    json_body: Any = None,
    data: bytes | None = None,
    headers: dict[str, str] | None = None,
    accept: tuple[int, ...] = (200, 201, 204),
) -> tuple[int, bytes, Any]:
    url = build_url(url, params)
    req_headers = dict(headers or {})
    # Cloudflare bans urllib's default Python-urllib User-Agent on some
    # provider APIs (Ramp returns 403 error code 1010).
    req_headers.setdefault("User-Agent", "Buoy/1.0")
    if token is not None:
        req_headers["Authorization"] = f"Bearer {token}"
    if json_body is not None:
        data = json.dumps(json_body, separators=(",", ":")).encode("utf-8")
        req_headers.setdefault("Content-Type", "application/json")
    req = urllib.request.Request(url, data=data, headers=req_headers, method=method)
    try:
        with urllib.request.urlopen(req) as response:
            body = response.read()
            status = response.getcode()
            if status not in accept:
                raise HTTPStatusError(status, body, response.headers)
            return status, body, response.headers
    except urllib.error.HTTPError as exc:
        body = exc.read()
        if exc.code in accept:
            return exc.code, body, exc.headers
        raise HTTPStatusError(exc.code, body, exc.headers) from None


def request_json(method: str, url: str, **kwargs: Any) -> Any:
    _, body, _ = request(method, url, **kwargs)
    if not body:
        return None
    try:
        return json.loads(body.decode("utf-8"))
    except json.JSONDecodeError:
        return body.decode("utf-8", errors="replace")


def request_text(method: str, url: str, **kwargs: Any) -> str:
    _, body, _ = request(method, url, **kwargs)
    return body.decode("utf-8", errors="replace")


def request_bytes(method: str, url: str, **kwargs: Any) -> bytes:
    _, body, _ = request(method, url, **kwargs)
    return body


def print_json(value: Any) -> None:
    print(json.dumps(value, indent=2, ensure_ascii=False))


def print_jsonl(values: Iterable[Any]) -> None:
    for value in values:
        print(json.dumps(value, separators=(",", ":"), ensure_ascii=False))


def write_bytes(path: str, data: bytes) -> dict[str, Any]:
    target = Path(path).expanduser()
    target.parent.mkdir(parents=True, exist_ok=True)
    target.write_bytes(data)
    return {"out": str(target), "bytes": len(data)}


def parse_rfc3339(value: str) -> datetime:
    normalized = value[:-1] + "+00:00" if value.endswith("Z") else value
    parsed = datetime.fromisoformat(normalized)
    if parsed.tzinfo is None:
        parsed = parsed.replace(tzinfo=timezone.utc)
    return parsed.astimezone(timezone.utc)


def iso_z(value: datetime) -> str:
    return value.astimezone(timezone.utc).isoformat().replace("+00:00", "Z")


def timezone_for(name: str | None) -> Any:
    if not name or ZoneInfo is None:
        return timezone.utc
    try:
        return ZoneInfo(name)
    except Exception:
        return timezone.utc


def b64url_decode(data: str | None) -> bytes:
    if not data:
        return b""
    data += "=" * ((4 - len(data) % 4) % 4)
    return base64.urlsafe_b64decode(data.encode("ascii"))


def b64url_encode(data: bytes) -> str:
    return base64.urlsafe_b64encode(data).decode("ascii").rstrip("=")


def email_raw(*, to: str, subject: str, body: str, headers: dict[str, str] | None = None) -> str:
    msg = EmailMessage()
    msg["To"] = to
    msg["Subject"] = subject
    for key, value in (headers or {}).items():
        if value:
            msg[key] = value
    msg.set_content(body)
    return b64url_encode(msg.as_bytes())


def header_map(message_or_payload: dict[str, Any]) -> dict[str, str]:
    payload = message_or_payload.get("payload", message_or_payload)
    return {h.get("name", "").lower(): h.get("value", "") for h in payload.get("headers", [])}


def gmail_permalink(message_id: str, account_email: str | None = None) -> str:
    email = account_email or env("ACCOUNT_EMAIL", "")
    auth = urllib.parse.quote(email) if email else "0"
    return f"https://mail.google.com/mail/?authuser={auth}#all/{message_id}"


def first_plain_text(part: dict[str, Any]) -> str:
    if part.get("mimeType") == "text/plain" and part.get("body", {}).get("data"):
        return b64url_decode(part["body"]["data"]).decode("utf-8", errors="replace")
    for child in part.get("parts", []) or []:
        text = first_plain_text(child)
        if text:
            return text
    return ""


def all_tabs(tabs: Iterable[dict[str, Any]]) -> Iterable[dict[str, Any]]:
    for tab in tabs or []:
        yield tab
        yield from all_tabs(tab.get("childTabs", []) or [])


def doc_tab_text(tab: dict[str, Any]) -> str:
    pieces: list[str] = []
    for block in tab.get("documentTab", {}).get("body", {}).get("content", []) or []:
        for element in block.get("paragraph", {}).get("elements", []) or []:
            pieces.append(element.get("textRun", {}).get("content", ""))
    return "".join(pieces)


def docs_blocks(tab: dict[str, Any]) -> list[dict[str, Any]]:
    blocks = []
    for block in tab.get("documentTab", {}).get("body", {}).get("content", []) or []:
        text = "".join(
            element.get("textRun", {}).get("content", "")
            for element in block.get("paragraph", {}).get("elements", []) or []
        )
        blocks.append({"startIndex": block.get("startIndex"), "endIndex": block.get("endIndex"), "text": text})
    return blocks


def slide_text(shape: dict[str, Any] | None) -> str:
    if not shape:
        return ""
    return "".join(
        element.get("textRun", {}).get("content", "")
        for element in shape.get("text", {}).get("textElements", []) or []
    )


def drive_query_literal(value: str) -> str:
    return value.replace("\\", "\\\\").replace("'", "\\'")


def file_size(path: str) -> int:
    return Path(path).expanduser().stat().st_size


def guess_mime(path: str) -> str:
    return mimetypes.guess_type(path)[0] or "application/octet-stream"
