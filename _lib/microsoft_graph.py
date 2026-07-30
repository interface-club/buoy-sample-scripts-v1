from __future__ import annotations

from email.utils import getaddresses
from urllib.parse import urlparse

from .google_api import *

BASE = "https://graph.microsoft.com/v1.0"


def graph_base() -> str:
    return env("BASE", BASE).rstrip("/")


def trusted_graph_url(url: str) -> str:
    candidate = urlparse(url)
    expected = urlparse(graph_base())
    if (
        candidate.scheme != expected.scheme
        or candidate.netloc != expected.netloc
        or not candidate.path.startswith(expected.path.rstrip("/") + "/")
    ):
        fail("Microsoft Graph continuation URL has an unexpected origin or API path")
    return url


def next_link(payload: dict[str, Any]) -> str | None:
    value = payload.get("@odata.nextLink")
    return value if isinstance(value, str) and value else None


def delta_link(payload: dict[str, Any]) -> str | None:
    value = payload.get("@odata.deltaLink")
    return value if isinstance(value, str) and value else None


def graph_headers(
    *,
    body_type: str | None = None,
    time_zone: str | None = None,
    etag: str | None = None,
    max_page_size: int | None = None,
) -> dict[str, str]:
    preferences: list[str] = []
    if body_type:
        preferences.append(f'outlook.body-content-type="{body_type}"')
    if time_zone:
        preferences.append(f'outlook.timezone="{time_zone}"')
    if max_page_size:
        preferences.append(f"odata.maxpagesize={max_page_size}")
    headers = {"Prefer": ", ".join(preferences)} if preferences else {}
    if etag:
        headers["If-Match"] = etag
    return headers


def email_recipients(value: str) -> list[dict[str, Any]]:
    parsed = getaddresses([value])
    recipients = []
    for name, address in parsed:
        if not address:
            continue
        email_address: dict[str, str] = {"address": address}
        if name:
            email_address["name"] = name
        recipients.append({"emailAddress": email_address})
    if not recipients:
        fail("At least one valid email recipient is required")
    return recipients


def json_recipients(value: Any) -> list[dict[str, Any]]:
    if value is None:
        return []
    if not isinstance(value, list):
        fail("Recipient JSON must be an array")
    recipients = []
    for item in value:
        if isinstance(item, str):
            recipients.extend(email_recipients(item))
            continue
        if not isinstance(item, dict):
            fail("Each recipient must be an email string or object")
        if isinstance(item.get("emailAddress"), dict):
            recipients.append(item)
            continue
        address = item.get("address") or item.get("email")
        if not isinstance(address, str) or not address:
            fail("Each recipient object must contain address or email")
        email_address = {"address": address}
        if isinstance(item.get("name"), str) and item["name"]:
            email_address["name"] = item["name"]
        recipients.append({"emailAddress": email_address})
    return recipients


def address_text(value: Any) -> str:
    if not isinstance(value, dict):
        return ""
    email_address = value.get("emailAddress")
    if not isinstance(email_address, dict):
        return ""
    name = email_address.get("name")
    address = email_address.get("address")
    if not isinstance(address, str):
        return ""
    return f"{name} <{address}>" if isinstance(name, str) and name else address


def address_list(values: Any) -> list[str]:
    return [text for text in (address_text(value) for value in values or []) if text]


def message_summary(message: dict[str, Any]) -> dict[str, Any]:
    return {
        "id": message.get("id"),
        "conversationId": message.get("conversationId"),
        "internetMessageId": message.get("internetMessageId"),
        "webLink": message.get("webLink"),
        "from": address_text(message.get("from") or message.get("sender")),
        "to": address_list(message.get("toRecipients")),
        "subject": message.get("subject") or "",
        "receivedDateTime": message.get("receivedDateTime"),
        "sentDateTime": message.get("sentDateTime"),
        "isRead": message.get("isRead"),
        "hasAttachments": message.get("hasAttachments"),
        "categories": message.get("categories") or [],
        "bodyPreview": message.get("bodyPreview") or "",
        "parentFolderId": message.get("parentFolderId"),
        "etag": message.get("@odata.etag"),
    }


def calendar_path(calendar_id: str, suffix: str = "") -> str:
    if calendar_id in {"", "primary"}:
        return f"{graph_base()}/me/calendar{suffix}"
    return f"{graph_base()}/me/calendars/{url_quote(calendar_id)}{suffix}"


def calendar_view_path(calendar_id: str) -> str:
    return calendar_path(calendar_id, "/calendarView")


def event_path(calendar_id: str, event_id: str) -> str:
    return calendar_path(calendar_id, f"/events/{url_quote(event_id)}")


def graph_datetime(value: Any) -> datetime | None:
    if not isinstance(value, dict) or not isinstance(value.get("dateTime"), str):
        return None
    raw = value["dateTime"]
    normalized = raw[:-1] + "+00:00" if raw.endswith("Z") else raw
    parsed = datetime.fromisoformat(normalized)
    if parsed.tzinfo is None:
        parsed = parsed.replace(tzinfo=timezone_for(value.get("timeZone")))
    return parsed.astimezone(timezone.utc)


def event_summary(
    event: dict[str, Any],
    calendar: dict[str, Any] | None = None,
) -> dict[str, Any]:
    location = event.get("location")
    return {
        "id": event.get("id"),
        "etag": event.get("@odata.etag"),
        "changeKey": event.get("changeKey"),
        "subject": event.get("subject") or "(No title)",
        "start": event.get("start"),
        "end": event.get("end"),
        "isAllDay": event.get("isAllDay", False),
        "isCancelled": event.get("isCancelled", False),
        "location": location.get("displayName") if isinstance(location, dict) else None,
        "webLink": event.get("webLink"),
        "organizer": event.get("organizer"),
        "attendees": event.get("attendees") or [],
        "calendarID": (calendar or {}).get("id"),
        "calendarName": (calendar or {}).get("name"),
        "calendarColor": (calendar or {}).get("hexColor") or (calendar or {}).get("color"),
    }
