from __future__ import annotations

import mimetypes
import uuid
from pathlib import Path
from typing import Any

from .google_api import *

BASE = "https://api.ramp.com/developer/v1"


def ramp_base() -> str:
    return env("RAMP_BASE_URL", BASE).rstrip("/")


def params(names: list[str]) -> dict[str, Any]:
    out: dict[str, Any] = {}
    for name in names:
        value = env(name.upper(), "")
        if value:
            out[name] = value
    if env("PAGE_SIZE", ""):
        out["page_size"] = env_int("PAGE_SIZE", 20)
    if env("START", ""):
        out["start"] = env("START")
    return out


def ramp_json(method: str, path: str, *, query: dict[str, Any] | None = None, body: Any = None, accept: tuple[int, ...] = (200, 201, 204)) -> Any:
    return request_json(method, f"{ramp_base()}{path}", token=access_token(), params=query, json_body=body, accept=accept)


def multipart_body(fields: dict[str, str], attachment_path: str, *, attachment_name: str = "attachment") -> tuple[bytes, str]:
    boundary = f"buoy_boundary_{uuid.uuid4().hex}"
    parts: list[bytes] = []
    for name, value in fields.items():
        if value == "":
            continue
        parts.append(f"--{boundary}\r\nContent-Disposition: form-data; name=\"{name}\"\r\n\r\n{value}\r\n".encode())
    path = Path(attachment_path).expanduser()
    content_type = mimetypes.guess_type(path.name)[0] or "application/octet-stream"
    parts.append(
        f"--{boundary}\r\nContent-Disposition: attachment; name=\"{attachment_name}\"; filename=\"{path.name}\"\r\nContent-Type: {content_type}\r\n\r\n".encode()
        + path.read_bytes()
        + b"\r\n"
    )
    parts.append(f"--{boundary}--\r\n".encode())
    return b"".join(parts), boundary


def get_business() -> None:
    print_json(ramp_json("GET", "/business"))


def list_users() -> None:
    print_json(ramp_json("GET", "/users", query=params(["employee_id", "role", "status", "entity_id", "department_id", "email", "location_id"])))


def list_reimbursements() -> None:
    print_json(ramp_json("GET", "/reimbursements", query=params([
        "direction",
        "state",
        "sync_status",
        "from_transaction_date",
        "to_transaction_date",
        "awaiting_approval_by_user_id",
        "has_been_approved",
        "trip_id",
        "accounting_field_selection_id",
        "entity_id",
        "from_date",
        "to_date",
        "from_submitted_at",
        "to_submitted_at",
        "synced_after",
        "sync_ready",
        "has_no_sync_commits",
        "updated_after",
        "user_id",
    ])))


def get_reimbursement() -> None:
    print_json(ramp_json("GET", f"/reimbursements/{url_quote(env('REIMBURSEMENT_ID', required=True))}"))


def create_mileage_reimbursement() -> None:
    body = env_json("BODY_JSON", None)
    if body is None:
        body = {
            "reimbursee_id": env("REIMBURSEE_ID", required=True),
            "trip_date": env("TRIP_DATE", required=True),
            "distance": env("DISTANCE", required=True),
        }
        for env_name, key in [
            ("DISTANCE_UNITS", "distance_units"),
            ("START_LOCATION", "start_location"),
            ("END_LOCATION", "end_location"),
            ("MEMO", "memo"),
            ("SPEND_ALLOCATION_ID", "spend_allocation_id"),
        ]:
            value = env(env_name, "")
            if value:
                body[key] = value
        waypoints = env_json("WAYPOINTS_JSON", None)
        if waypoints is not None:
            body["waypoints"] = waypoints
    print_json(ramp_json("POST", "/reimbursements/mileage", body=body))


def submit_reimbursement_receipt() -> None:
    fields = {
        "idempotency_key": env("IDEMPOTENCY_KEY", required=True),
        "reimbursee_id": env("REIMBURSEE_ID", required=True),
        "reimbursement_id": env("REIMBURSEMENT_ID", ""),
    }
    receipt_path = env("RECEIPT_PATH", "")
    if receipt_path:
        body, boundary = multipart_body(fields, receipt_path, attachment_name="receipt")
        print_json(request_json(
            "POST",
            f"{ramp_base()}/reimbursements/submit-receipt",
            token=access_token(),
            headers={"Content-Type": f"multipart/form-data; boundary={boundary}"},
            data=body,
            accept=(200, 201),
        ))
    else:
        print_json(ramp_json("POST", "/reimbursements/submit-receipt", body={key: value for key, value in fields.items() if value}))


def approve_blank_canvas_approval() -> None:
    body = env_json("BODY_JSON", None) or {"action": env("ACTION", required=True)}
    print_json(ramp_json("POST", f"/blank-canvas-approvals/{url_quote(env('APPROVAL_TRIGGER_INSTANCE_ID', required=True))}", body=body))


def update_blank_canvas_approval_metadata() -> None:
    print_json(ramp_json("PATCH", f"/blank-canvas-approvals/{url_quote(env('APPROVAL_TRIGGER_INSTANCE_ID', required=True))}/metadata", body=env_json("BODY_JSON", required=True)))


def list_funds() -> None:
    print_json(ramp_json("GET", "/funds", query=params([
        "display_name",
        "spend_program_id",
        "entity_id",
        "created_after",
        "created_before",
        "card_id",
        "user_id",
        "is_terminated",
        "member_roles",
    ])))


def get_fund() -> None:
    print_json(ramp_json("GET", f"/funds/{url_quote(env('FUND_ID', required=True))}"))


def create_fund() -> None:
    body = env_json("BODY_JSON", None)
    if body is None:
        body = {"user_id": env("USER_ID", required=True)}
        for env_name, key in [
            ("DISPLAY_NAME", "display_name"),
            ("SPEND_PROGRAM_ID", "spend_program_id"),
        ]:
            value = env(env_name, "")
            if value:
                body[key] = value
        if env("IS_SHAREABLE", ""):
            body["is_shareable"] = env_bool("IS_SHAREABLE", False)
        for env_name, key in [
            ("PERMITTED_SPEND_TYPES_JSON", "permitted_spend_types"),
            ("SPENDING_RESTRICTIONS_JSON", "spending_restrictions"),
            ("ACCOUNTING_RULES_JSON", "accounting_rules"),
        ]:
            value = env_json(env_name, None)
            if value is not None:
                body[key] = value
    print_json(ramp_json("POST", "/funds", body=body))


def update_fund() -> None:
    print_json(ramp_json("PATCH", f"/funds/{url_quote(env('FUND_ID', required=True))}", body=env_json("BODY_JSON", required=True)))


def add_fund_members() -> None:
    print_json(ramp_json("POST", f"/funds/{url_quote(env('FUND_ID', required=True))}/members", body={"user_ids": env_json("USER_IDS_JSON", required=True)}))


def remove_fund_members() -> None:
    print_json(ramp_json("DELETE", f"/funds/{url_quote(env('FUND_ID', required=True))}/members", body={"user_ids": env_json("USER_IDS_JSON", required=True)}))


def suspend_fund() -> None:
    print_json(ramp_json("POST", f"/funds/{url_quote(env('FUND_ID', required=True))}/suspension"))


def unsuspend_fund() -> None:
    print_json(ramp_json("DELETE", f"/funds/{url_quote(env('FUND_ID', required=True))}/suspension"))


def terminate_fund() -> None:
    print_json(ramp_json("DELETE", f"/funds/{url_quote(env('FUND_ID', required=True))}", accept=(200, 202, 204)))


def list_virtual_cards() -> None:
    print_json(ramp_json("GET", "/cards/virtual", query=params(["entity_id", "user_id", "is_terminated"])))


def get_virtual_card() -> None:
    print_json(ramp_json("GET", f"/cards/virtual/{url_quote(env('CARD_ID', required=True))}"))


def create_vault_card() -> None:
    print_json(ramp_json("POST", "/cards/vault", body=env_json("BODY_JSON", required=True)))


def get_vault_card() -> None:
    print_json(ramp_json("GET", f"/cards/vault/{url_quote(env('CARD_ID', required=True))}"))


def create_embedded_card_token() -> None:
    print_json(ramp_json("POST", f"/embedded/cards/{url_quote(env('CARD_ID', required=True))}/embed", body={"parent_origin": env("PARENT_ORIGIN", required=True)}))
