from __future__ import annotations

from .microsoft_graph import *

CALENDAR_SELECT = (
    "id,name,color,hexColor,isDefaultCalendar,canEdit,canShare,"
    "canViewPrivateItems,changeKey,owner"
)
EVENT_SELECT = (
    "id,changeKey,subject,body,bodyPreview,start,end,isAllDay,"
    "isCancelled,location,locations,webLink,organizer,attendees,recurrence,"
    "seriesMasterId,type,originalStart,reminderMinutesBeforeStart,"
    "isReminderOn,isOnlineMeeting,onlineMeeting,onlineMeetingProvider,"
    "responseStatus,showAs,sensitivity,importance"
)


def list_calendars() -> None:
    page_url = active_page_token()
    params = None
    if not page_url:
        page_url = f"{graph_base()}/me/calendars"
        params = {
            "$select": CALENDAR_SELECT,
            "$top": min(max(env_int("PAGE_SIZE", 100), 1), 999),
        }
    else:
        page_url = trusted_graph_url(page_url)
    payload = request_json("GET", page_url, token=access_token(), params=params)
    print_json(
        {
            "calendars": [_calendar_summary(item) for item in payload.get("value", [])],
            "nextPageToken": next_link(payload),
        }
    )


def list_events() -> None:
    calendar_id = env("CALENDAR_ID", "primary")
    time_min = env("TIME_MIN", required=True)
    time_max = env("TIME_MAX", required=True)
    time_zone = env("TIME_ZONE", "UTC")
    query = env("QUERY", "").casefold()
    calendar = _get_calendar(calendar_id)
    url = calendar_view_path(calendar_id)
    params: dict[str, Any] | None = {
        "startDateTime": time_min,
        "endDateTime": time_max,
        "$select": EVENT_SELECT,
        "$orderby": "start/dateTime",
        "$top": min(max(env_int("MAX_RESULTS", 250), 1), 1000),
    }
    events = []
    while url:
        payload = request_json(
            "GET",
            url,
            token=access_token(),
            params=params,
            headers=graph_headers(time_zone=time_zone, body_type="text"),
        )
        params = None
        for event in payload.get("value", []):
            searchable = " ".join(
                str(event.get(key) or "")
                for key in ("subject", "bodyPreview")
            ).casefold()
            if not query or query in searchable:
                events.append(event_summary(event, calendar))
        next_url = next_link(payload)
        url = trusted_graph_url(next_url) if next_url else ""
    events.sort(key=lambda item: _sort_datetime(item.get("start")))
    print_json({"calendar": _calendar_summary(calendar), "events": events})


def find_next_upcoming_event() -> None:
    time_min = env("TIME_MIN", iso_z(datetime.now(timezone.utc)))
    lower_bound = parse_rfc3339(time_min)
    time_max = env("TIME_MAX", iso_z(lower_bound + timedelta(days=30)))
    events_per_calendar = max(2, env_int("EVENTS_PER_CALENDAR", 10))
    include_all_day = env_bool("INCLUDE_ALL_DAY", True)
    time_zone = env("TIME_ZONE", "UTC")
    calendar_ids = env_json("CALENDAR_IDS_JSON", None)
    if calendar_ids is not None and (
        not isinstance(calendar_ids, list)
        or not all(isinstance(item, str) and item for item in calendar_ids)
    ):
        fail("CALENDAR_IDS_JSON must be an array of calendar IDs")
    calendars = (
        [_get_calendar(calendar_id) for calendar_id in calendar_ids]
        if calendar_ids
        else _all_calendars()
    )
    candidates = []
    for calendar in calendars:
        calendar_id = calendar.get("id")
        if not isinstance(calendar_id, str) or not calendar_id:
            continue
        url = calendar_view_path(calendar_id)
        params: dict[str, Any] | None = {
            "startDateTime": time_min,
            "endDateTime": time_max,
            "$select": EVENT_SELECT,
            "$orderby": "start/dateTime",
            "$top": min(events_per_calendar, 1000),
        }
        accepted = 0
        while url and accepted < events_per_calendar:
            payload = request_json(
                "GET",
                url,
                token=access_token(),
                params=params,
                headers=graph_headers(time_zone=time_zone),
            )
            params = None
            for event in payload.get("value", []):
                if event.get("isCancelled"):
                    continue
                is_all_day = bool(event.get("isAllDay"))
                if is_all_day and not include_all_day:
                    continue
                instant = graph_datetime(event.get("start"))
                if instant is None or instant < lower_bound:
                    continue
                candidates.append((instant, is_all_day, calendar, event))
                accepted += 1
            next_url = next_link(payload)
            url = trusted_graph_url(next_url) if next_url else ""
    candidates.sort(key=lambda item: item[0])
    if not candidates:
        print_json(None)
        return
    instant, is_all_day, calendar, event = candidates[0]
    result = event_summary(event, calendar)
    result.update(
        {
            "startInstant": iso_z(instant),
            "isAllDay": is_all_day,
        }
    )
    print_json(result)


def get_event_details() -> None:
    calendar_id = env("CALENDAR_ID", "primary")
    event_id = env("EVENT_ID", required=True)
    event = request_json(
        "GET",
        event_path(calendar_id, event_id),
        token=access_token(),
        params={"$select": EVENT_SELECT},
        headers=graph_headers(
            body_type=env("BODY_CONTENT_TYPE", "text"),
            time_zone=env("TIME_ZONE", "UTC"),
        ),
    )
    print_json({key: event.get(key) for key in _event_detail_keys()})


def check_free_busy() -> None:
    schedules = env_json("SCHEDULES_JSON", None)
    if schedules is None:
        profile = request_json(
            "GET",
            f"{graph_base()}/me",
            token=access_token(),
            params={"$select": "mail,userPrincipalName"},
        )
        schedules = [profile.get("mail") or profile.get("userPrincipalName")]
    if not isinstance(schedules, list) or not all(
        isinstance(item, str) and item for item in schedules
    ):
        fail("SCHEDULES_JSON must be an array of email addresses")
    time_zone = env("TIME_ZONE", "UTC")
    body = {
        "schedules": schedules,
        "startTime": {
            "dateTime": env("TIME_MIN", required=True),
            "timeZone": time_zone,
        },
        "endTime": {
            "dateTime": env("TIME_MAX", required=True),
            "timeZone": time_zone,
        },
        "availabilityViewInterval": min(
            max(env_int("AVAILABILITY_INTERVAL", 30), 5),
            1440,
        ),
    }
    payload = request_json(
        "POST",
        f"{graph_base()}/me/calendar/getSchedule",
        token=access_token(),
        json_body=body,
    )
    print_json(
        {
            item.get("scheduleId"): item
            for item in payload.get("value", [])
            if item.get("scheduleId")
        }
    )


def create_event() -> None:
    body = env_json("EVENT_JSON", {}) or {}
    if not isinstance(body, dict):
        fail("EVENT_JSON must be a JSON object")
    body = _normalize_event_patch(body)
    all_day = env_bool("ALL_DAY", False)
    time_zone = env("TIME_ZONE", "UTC")
    if "subject" not in body:
        body["subject"] = env("SUMMARY", required=True)
    if "start" not in body or "end" not in body:
        start = env("START", "")
        end = env("END", "")
        if not start or not end:
            fail("START and END are required unless EVENT_JSON supplies start and end")
        body["start"] = _date_time_time_zone(start, time_zone, all_day)
        body["end"] = _date_time_time_zone(end, time_zone, all_day)
    body.setdefault("isAllDay", all_day)
    location = env("LOCATION", "")
    if location:
        body["location"] = {"displayName": location}
    description = env("DESCRIPTION", "")
    if description:
        body["body"] = {
            "contentType": env("BODY_CONTENT_TYPE", "text"),
            "content": description,
        }
    if "attendees" not in body:
        body["attendees"] = _event_attendees(env_json("ATTENDEES_JSON", []))
    recurrence = env_json("RECURRENCE_JSON", None)
    if recurrence is not None:
        body["recurrence"] = recurrence
    if "REMINDER_MINUTES" in os.environ:
        body["isReminderOn"] = True
        body["reminderMinutesBeforeStart"] = env_int("REMINDER_MINUTES", 15)
    if env_bool("IS_ONLINE_MEETING", False):
        body["isOnlineMeeting"] = True
        body["onlineMeetingProvider"] = env(
            "ONLINE_MEETING_PROVIDER",
            "teamsForBusiness",
        )
    transaction_id = env("TRANSACTION_ID", "")
    if transaction_id:
        body["transactionId"] = transaction_id
    result = request_json(
        "POST",
        calendar_path(env("CALENDAR_ID", "primary"), "/events"),
        token=access_token(),
        json_body=body,
        headers=graph_headers(time_zone=time_zone),
    )
    print_json(event_summary(result))


def update_event() -> None:
    calendar_id = env("CALENDAR_ID", "primary")
    event_id = env("EVENT_ID", required=True)
    current = request_json(
        "GET",
        event_path(calendar_id, event_id),
        token=access_token(),
        params={"$select": EVENT_SELECT},
    )
    patch = env_json("PATCH_JSON", {}) or {}
    if not isinstance(patch, dict):
        fail("PATCH_JSON must be a JSON object")
    patch = _normalize_event_patch(patch)
    subject = env("NEW_SUMMARY", "")
    if subject:
        patch["subject"] = subject
    location = env("NEW_LOCATION", "")
    if location:
        patch["location"] = {"displayName": location}
    if not patch:
        fail("Provide PATCH_JSON, NEW_SUMMARY, or NEW_LOCATION")
    result = request_json(
        "PATCH",
        event_path(calendar_id, event_id),
        token=access_token(),
        headers=graph_headers(etag=current.get("@odata.etag")),
        json_body=patch,
    )
    print_json(
        {
            "before": event_summary(current),
            "after": event_summary(result),
        }
    )


def update_event_guests() -> None:
    calendar_id = env("CALENDAR_ID", "primary")
    event_id = env("EVENT_ID", required=True)
    current = request_json(
        "GET",
        event_path(calendar_id, event_id),
        token=access_token(),
        params={"$select": EVENT_SELECT},
    )
    remove_items = env_json("REMOVE_EMAILS_JSON", [])
    add_items = env_json("ADD_EMAILS_JSON", [])
    if "REMOVE_EMAILS_JSON" not in os.environ and "ADD_EMAILS_JSON" not in os.environ:
        fail("Provide ADD_EMAILS_JSON or REMOVE_EMAILS_JSON")
    if not isinstance(remove_items, list) or not all(
        isinstance(item, str) for item in remove_items
    ):
        fail("REMOVE_EMAILS_JSON must be an array of email addresses")
    remove = {item.casefold() for item in remove_items}
    attendees = [
        attendee
        for attendee in current.get("attendees", [])
        if _attendee_address(attendee).casefold() not in remove
    ]
    seen = {_attendee_address(attendee).casefold() for attendee in attendees}
    for attendee in _event_attendees(add_items):
        address = _attendee_address(attendee).casefold()
        if address and address not in seen:
            attendees.append(attendee)
            seen.add(address)
    result = request_json(
        "PATCH",
        event_path(calendar_id, event_id),
        token=access_token(),
        headers=graph_headers(etag=current.get("@odata.etag")),
        json_body={"attendees": attendees},
    )
    print_json(
        {
            "preview": {
                **event_summary(current),
                "attendees": attendees,
            },
            "after": event_summary(result),
        }
    )


def delete_event() -> None:
    calendar_id = env("CALENDAR_ID", "primary")
    event_id = env("EVENT_ID", required=True)
    current = request_json(
        "GET",
        event_path(calendar_id, event_id),
        token=access_token(),
        params={"$select": EVENT_SELECT},
    )
    status, body, _ = request(
        "DELETE",
        event_path(calendar_id, event_id),
        token=access_token(),
        headers=graph_headers(etag=current.get("@odata.etag")),
    )
    print_json(
        {
            "deleted": body == b"",
            "status": status,
            "preview": event_summary(current),
        }
    )


def initial_event_sync() -> None:
    _require_primary_calendar()
    time_min = env("TIME_MIN", required=True)
    time_max = env("TIME_MAX", required=True)
    time_zone = env("TIME_ZONE", "UTC")
    url = f"{graph_base()}/me/calendarView/delta"
    params: dict[str, Any] | None = {
        "startDateTime": time_min,
        "endDateTime": time_max,
    }
    events = []
    final_delta_link = None
    while url:
        payload = request_json(
            "GET",
            url,
            token=access_token(),
            params=params,
            headers=graph_headers(
                time_zone=time_zone,
                max_page_size=min(max(env_int("PAGE_SIZE", 250), 1), 999),
            ),
        )
        params = None
        events.extend(payload.get("value", []))
        final_delta_link = delta_link(payload) or final_delta_link
        next_url = next_link(payload)
        url = trusted_graph_url(next_url) if next_url else ""
    print_json({"events": events, "nextDeltaLink": final_delta_link})


def incremental_event_sync() -> None:
    _require_primary_calendar()
    delta_url = env("DELTA_LINK", "") or env("SYNC_TOKEN", "")
    if not delta_url:
        fail("DELTA_LINK is required")
    url = trusted_graph_url(delta_url)
    events = []
    final_delta_link = None
    try:
        while url:
            payload = request_json(
                "GET",
                url,
                token=access_token(),
                headers=graph_headers(
                    time_zone=env("TIME_ZONE", "UTC"),
                    max_page_size=min(max(env_int("PAGE_SIZE", 250), 1), 999),
                ),
            )
            events.extend(payload.get("value", []))
            final_delta_link = delta_link(payload) or final_delta_link
            next_url = next_link(payload)
            url = trusted_graph_url(next_url) if next_url else ""
    except HTTPStatusError as error:
        if error.status == 410:
            print("DELTA_LINK_EXPIRED_FULL_SYNC_REQUIRED", file=sys.stderr)
            raise SystemExit(2)
        raise
    print_json({"events": events, "nextDeltaLink": final_delta_link})


def _calendar_summary(calendar: dict[str, Any]) -> dict[str, Any]:
    return {
        "id": calendar.get("id"),
        "name": calendar.get("name"),
        "color": calendar.get("color"),
        "hexColor": calendar.get("hexColor"),
        "isDefaultCalendar": calendar.get("isDefaultCalendar", False),
        "canEdit": calendar.get("canEdit", False),
        "canShare": calendar.get("canShare", False),
        "canViewPrivateItems": calendar.get("canViewPrivateItems", False),
        "owner": calendar.get("owner"),
    }


def _get_calendar(calendar_id: str) -> dict[str, Any]:
    return request_json(
        "GET",
        calendar_path(calendar_id),
        token=access_token(),
        params={"$select": CALENDAR_SELECT},
    )


def _all_calendars() -> list[dict[str, Any]]:
    url = f"{graph_base()}/me/calendars"
    params: dict[str, Any] | None = {
        "$select": CALENDAR_SELECT,
        "$top": 999,
    }
    calendars = []
    while url:
        payload = request_json("GET", url, token=access_token(), params=params)
        params = None
        calendars.extend(payload.get("value", []))
        next_url = next_link(payload)
        url = trusted_graph_url(next_url) if next_url else ""
    return calendars


def _normalize_event_patch(body: dict[str, Any]) -> dict[str, Any]:
    normalized = dict(body)
    if "summary" in normalized and "subject" not in normalized:
        normalized["subject"] = normalized.pop("summary")
    if "description" in normalized and "body" not in normalized:
        normalized["body"] = {
            "contentType": "text",
            "content": normalized.pop("description"),
        }
    if isinstance(normalized.get("location"), str):
        normalized["location"] = {"displayName": normalized["location"]}
    if "attendees" in normalized:
        normalized["attendees"] = _event_attendees(normalized["attendees"])
    for key in ("start", "end"):
        value = normalized.get(key)
        if isinstance(value, dict) and "date" in value and "dateTime" not in value:
            normalized[key] = {
                "dateTime": f"{value['date']}T00:00:00",
                "timeZone": value.get("timeZone") or "UTC",
            }
            normalized.setdefault("isAllDay", True)
    return normalized


def _event_attendees(value: Any) -> list[dict[str, Any]]:
    if value is None:
        return []
    if not isinstance(value, list):
        fail("Attendees must be a JSON array")
    attendees = []
    for item in value:
        attendee_type = "required"
        if isinstance(item, str):
            recipient = email_recipients(item)[0]
        elif isinstance(item, dict):
            attendee_type = str(item.get("type") or "required")
            if isinstance(item.get("emailAddress"), dict):
                recipient = {"emailAddress": item["emailAddress"]}
            else:
                address = item.get("address") or item.get("email")
                if not isinstance(address, str) or not address:
                    fail("Each attendee must contain email, address, or emailAddress")
                email_address = {"address": address}
                if isinstance(item.get("name"), str) and item["name"]:
                    email_address["name"] = item["name"]
                recipient = {"emailAddress": email_address}
        else:
            fail("Each attendee must be an email string or object")
        attendees.append({**recipient, "type": attendee_type})
    return attendees


def _attendee_address(attendee: Any) -> str:
    if not isinstance(attendee, dict):
        return ""
    email_address = attendee.get("emailAddress")
    if not isinstance(email_address, dict):
        return ""
    address = email_address.get("address")
    return address if isinstance(address, str) else ""


def _date_time_time_zone(
    value: str,
    time_zone: str,
    all_day: bool,
) -> dict[str, str]:
    if all_day and "T" not in value:
        value = f"{value}T00:00:00"
    return {"dateTime": value, "timeZone": time_zone}


def _sort_datetime(value: Any) -> str:
    parsed = graph_datetime(value)
    return iso_z(parsed) if parsed else ""


def _event_detail_keys() -> list[str]:
    return [
        "id",
        "@odata.etag",
        "changeKey",
        "subject",
        "body",
        "bodyPreview",
        "location",
        "locations",
        "start",
        "end",
        "isAllDay",
        "isCancelled",
        "recurrence",
        "seriesMasterId",
        "type",
        "originalStart",
        "organizer",
        "attendees",
        "responseStatus",
        "isReminderOn",
        "reminderMinutesBeforeStart",
        "isOnlineMeeting",
        "onlineMeeting",
        "onlineMeetingProvider",
        "showAs",
        "sensitivity",
        "importance",
        "webLink",
    ]


def _require_primary_calendar() -> None:
    if env("CALENDAR_ID", "primary") not in {"", "primary"}:
        fail("Microsoft Graph calendarView delta sync supports only the primary calendar")
