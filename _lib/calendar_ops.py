from __future__ import annotations

from .google_api import *

BASE = "https://www.googleapis.com/calendar/v3"


def cal_path(calendar_id: str, suffix: str = "") -> str:
    return f"{BASE}/calendars/{url_quote(calendar_id)}{suffix}"


def event_summary(event: dict[str, Any], calendar: dict[str, Any] | None = None, colors: dict[str, Any] | None = None) -> dict[str, Any]:
    calendar_color = (calendar or {}).get("backgroundColor")
    color_id = event.get("colorId")
    event_color = None
    if color_id and colors:
        event_color = (colors.get(color_id) or {}).get("background")
    return {
        "id": event.get("id"),
        "etag": event.get("etag"),
        "status": event.get("status"),
        "summary": event.get("summary"),
        "start": event.get("start"),
        "end": event.get("end"),
        "location": event.get("location"),
        "htmlLink": event.get("htmlLink"),
        "colorId": color_id,
        "calendarColorHex": calendar_color,
        "eventColorHex": event_color or calendar_color,
        "attendees": [a.get("email") for a in event.get("attendees", []) or [] if a.get("email")],
        "organizer": event.get("organizer"),
        "creator": event.get("creator"),
    }


def list_calendars() -> None:
    min_role = env("MIN_ACCESS_ROLE", "reader")
    params = {
        "maxResults": min(env_int("PAGE_SIZE", 250), 250),
        "minAccessRole": min_role,
    }
    if active_page_token():
        params["pageToken"] = active_page_token()
    payload = request_json(
        "GET", f"{BASE}/users/me/calendarList", token=access_token(), params=params
    )
    calendars = [
        {
            "id": calendar.get("id"),
            "summary": calendar.get("summary"),
            "primary": calendar.get("primary", False),
            "accessRole": calendar.get("accessRole"),
            "timeZone": calendar.get("timeZone"),
            "selected": calendar.get("selected", False),
        }
        for calendar in payload.get("items", [])
    ]
    print_json(
        {
            "calendars": calendars,
            "nextPageToken": payload.get("nextPageToken"),
        }
    )


def list_events() -> None:
    calendar_id = env("CALENDAR_ID", "primary")
    time_min = env("TIME_MIN", required=True)
    time_max = env("TIME_MAX", required=True)
    query = env("QUERY", "")
    calendar = request_json("GET", f"{BASE}/users/me/calendarList/{url_quote(calendar_id)}", token=access_token(), params={"fields": "id,summary,backgroundColor,timeZone"})
    colors = request_json("GET", f"{BASE}/colors", token=access_token(), params={"fields": "event"}).get("event", {})
    page_token = env("PAGE_TOKEN", "")
    events = []
    while True:
        params = {"timeMin": time_min, "timeMax": time_max, "singleEvents": True, "orderBy": "startTime", "maxResults": env_int("MAX_RESULTS", 250), "fields": "items(id,etag,status,summary,start,end,location,htmlLink,colorId,attendees(email,responseStatus),organizer(email,displayName),creator(email,displayName)),nextPageToken,nextSyncToken"}
        if query:
            params["q"] = query
        if page_token:
            params["pageToken"] = page_token
        payload = request_json("GET", cal_path(calendar_id, "/events"), token=access_token(), params=params)
        events.extend(event_summary(event, calendar, colors) for event in payload.get("items", []))
        page_token = payload.get("nextPageToken") or ""
        if not page_token:
            print_json({"calendar": calendar, "events": events, "nextSyncToken": payload.get("nextSyncToken")})
            return


def find_next_upcoming_event() -> None:
    time_min = env("TIME_MIN", iso_z(datetime.now(timezone.utc)))
    lower_bound = parse_rfc3339(time_min)
    time_max = env("TIME_MAX", iso_z(lower_bound + timedelta(days=30)))
    events_per_calendar = max(2, env_int("EVENTS_PER_CALENDAR", 10))
    include_all_day = env_bool("INCLUDE_ALL_DAY", True)
    calendar_ids = env_json("CALENDAR_IDS_JSON", None)
    if calendar_ids:
        calendars = [request_json("GET", cal_path(calendar_id), token=access_token(), params={"fields": "id,summary,timeZone,backgroundColor"}) for calendar_id in calendar_ids]
    else:
        payload = request_json("GET", f"{BASE}/users/me/calendarList", token=access_token(), params={"maxResults": 250, "minAccessRole": "reader", "fields": "items(id,summary,primary,selected,hidden,timeZone,backgroundColor),nextPageToken"})
        all_cals = [c for c in payload.get("items", []) if not c.get("hidden", False)]
        calendars = [c for c in all_cals if c.get("primary") or c.get("selected")] or all_cals
    candidates = []
    for calendar in calendars:
        payload = request_json("GET", cal_path(calendar["id"], "/events"), token=access_token(), params={"timeMin": time_min, "timeMax": time_max, "singleEvents": True, "orderBy": "startTime", "maxResults": events_per_calendar, "fields": "items(id,status,summary,start,end,location,htmlLink,attendees(email,responseStatus),organizer(email,displayName),creator(email,displayName))"})
        for event in payload.get("items", []):
            if event.get("status") == "cancelled":
                continue
            start = event.get("start", {})
            is_all_day = "dateTime" not in start
            if is_all_day:
                if not include_all_day or not start.get("date"):
                    continue
                instant = datetime.combine(date.fromisoformat(start["date"]), dtime.min, timezone_for(calendar.get("timeZone"))).astimezone(timezone.utc)
            else:
                instant = parse_rfc3339(start["dateTime"])
            if instant >= lower_bound:
                candidates.append((instant, is_all_day, calendar, event))
    candidates.sort(key=lambda item: item[0])
    if not candidates:
        print_json(None)
        return
    instant, is_all_day, calendar, event = candidates[0]
    print_json({"calendarID": calendar.get("id"), "calendarSummary": calendar.get("summary"), "calendarColorHex": calendar.get("backgroundColor"), "id": event.get("id"), "summary": event.get("summary", "(No title)"), "startInstant": iso_z(instant), "isAllDay": is_all_day, "start": event.get("start"), "end": event.get("end"), "location": event.get("location"), "htmlLink": event.get("htmlLink"), "organizer": event.get("organizer"), "attendees": event.get("attendees", [])})


def get_event_details() -> None:
    event = request_json("GET", cal_path(env("CALENDAR_ID", "primary"), f"/events/{url_quote(env('EVENT_ID', required=True))}"), token=access_token())
    keys = ["id", "etag", "status", "summary", "description", "location", "start", "end", "recurrence", "recurringEventId", "originalStartTime", "organizer", "creator", "attendees", "reminders", "conferenceData", "htmlLink"]
    print_json({key: event.get(key) for key in keys})


def check_free_busy() -> None:
    ids = env_json("CALENDAR_IDS_JSON", ["primary"])
    body = {"timeMin": env("TIME_MIN", required=True), "timeMax": env("TIME_MAX", required=True), "timeZone": env("TIME_ZONE", "UTC"), "calendarExpansionMax": 50, "items": [{"id": item} for item in ids]}
    print_json(request_json("POST", f"{BASE}/freeBusy", token=access_token(), json_body=body).get("calendars", {}))


def create_event() -> None:
    body = env_json("EVENT_JSON", {}) or {}
    all_day = env_bool("ALL_DAY", False)
    start_value = env("START", "")
    end_value = env("END", "")
    tz = env("TIME_ZONE", "UTC")
    if "summary" not in body:
        body["summary"] = env("SUMMARY", required=True)
    if "start" not in body or "end" not in body:
        if not start_value or not end_value:
            fail("START and END are required unless EVENT_JSON supplies start and end")
        if all_day:
            body["start"] = {"date": start_value}
            body["end"] = {"date": end_value}
        else:
            body["start"] = {"dateTime": start_value, "timeZone": tz}
            body["end"] = {"dateTime": end_value, "timeZone": tz}
    if env("LOCATION", ""):
        body["location"] = env("LOCATION")
    if env("DESCRIPTION", ""):
        body["description"] = env("DESCRIPTION")
    if "attendees" not in body:
        body["attendees"] = env_json("ATTENDEES_JSON", [])
    if "reminders" not in body:
        body["reminders"] = env_json("REMINDERS_JSON", {"useDefault": True})
    recurrence = env_json("RECURRENCE_JSON", None)
    if recurrence is not None:
        body["recurrence"] = recurrence
    conference_data = env_json("CONFERENCE_DATA_JSON", None)
    if conference_data is not None:
        body["conferenceData"] = conference_data
    params = {"sendUpdates": env("SEND_UPDATES", "all")}
    if env("CONFERENCE_DATA_VERSION", ""):
        params["conferenceDataVersion"] = env("CONFERENCE_DATA_VERSION")
    result = request_json("POST", cal_path(env("CALENDAR_ID", "primary"), "/events"), token=access_token(), params=params, json_body=body)
    print_json({key: result.get(key) for key in ["id", "summary", "start", "end", "attendees", "htmlLink", "hangoutLink", "conferenceData", "etag"]})


def update_event() -> None:
    calendar_id = env("CALENDAR_ID", "primary")
    event_id = env("EVENT_ID", required=True)
    current = request_json("GET", cal_path(calendar_id, f"/events/{url_quote(event_id)}"), token=access_token())
    patch = env_json("PATCH_JSON", {}) or {}
    if env("NEW_SUMMARY", ""):
        patch["summary"] = env("NEW_SUMMARY")
    if env("NEW_LOCATION", ""):
        patch["location"] = env("NEW_LOCATION")
    params = {"sendUpdates": env("SEND_UPDATES", "all")}
    if env("CONFERENCE_DATA_VERSION", ""):
        params["conferenceDataVersion"] = env("CONFERENCE_DATA_VERSION")
    result = request_json("PATCH", cal_path(calendar_id, f"/events/{url_quote(event_id)}"), token=access_token(), params=params, headers={"If-Match": current.get("etag", "")}, json_body=patch)
    print_json({"before": {key: current.get(key) for key in ["id", "summary", "start", "end", "attendees", "htmlLink", "etag"]}, "after": {key: result.get(key) for key in ["id", "summary", "start", "end", "location", "attendees", "htmlLink", "hangoutLink", "conferenceData", "etag"]}})


def update_event_guests() -> None:
    calendar_id = env("CALENDAR_ID", "primary")
    event_id = env("EVENT_ID", required=True)
    current = request_json("GET", cal_path(calendar_id, f"/events/{url_quote(event_id)}"), token=access_token())
    remove = set(env_json("REMOVE_EMAILS_JSON", []))
    add_items = env_json("ADD_EMAILS_JSON", [])
    attendees = [a for a in current.get("attendees", []) if a.get("email") not in remove]
    seen = {a.get("email") for a in attendees}
    for item in add_items:
        attendee = item if isinstance(item, dict) else {"email": item}
        if attendee.get("email") not in seen:
            attendees.append(attendee)
            seen.add(attendee.get("email"))
    updated = dict(current)
    updated["attendees"] = attendees
    result = request_json("PUT", cal_path(calendar_id, f"/events/{url_quote(event_id)}"), token=access_token(), params={"sendUpdates": env("SEND_UPDATES", "all")}, headers={"If-Match": current.get("etag", "")}, json_body=updated)
    print_json({"preview": {key: updated.get(key) for key in ["id", "summary", "start", "end", "attendees"]}, "after": {key: result.get(key) for key in ["id", "summary", "attendees", "htmlLink", "etag"]}})


def delete_event() -> None:
    calendar_id = env("CALENDAR_ID", "primary")
    event_id = env("EVENT_ID", required=True)
    current = request_json("GET", cal_path(calendar_id, f"/events/{url_quote(event_id)}"), token=access_token())
    status, body, _ = request("DELETE", cal_path(calendar_id, f"/events/{url_quote(event_id)}"), token=access_token(), params={"sendUpdates": env("SEND_UPDATES", "all")}, headers={"If-Match": current.get("etag", "")})
    print_json({"deleted": body == b"", "status": status, "preview": {key: current.get(key) for key in ["id", "summary", "start", "end", "attendees", "htmlLink", "etag"]}})


def initial_event_sync() -> None:
    calendar_id = env("CALENDAR_ID", "primary")
    page_token = env("PAGE_TOKEN", "")
    events = []
    sync_token = None
    while True:
        params = {"maxResults": 250, "singleEvents": True, "showDeleted": True}
        if page_token:
            params["pageToken"] = page_token
        payload = request_json("GET", cal_path(calendar_id, "/events"), token=access_token(), params=params)
        events.extend(payload.get("items", []))
        page_token = payload.get("nextPageToken") or ""
        sync_token = payload.get("nextSyncToken") or sync_token
        if not page_token:
            break
    print_json({"events": events, "nextSyncToken": sync_token})


def incremental_event_sync() -> None:
    calendar_id = env("CALENDAR_ID", "primary")
    sync_token = env("SYNC_TOKEN", required=True)
    page_token = env("PAGE_TOKEN", "")
    events = []
    new_sync_token = None
    try:
        while True:
            params = {"maxResults": 250, "singleEvents": True, "showDeleted": True, "syncToken": sync_token}
            if page_token:
                params["pageToken"] = page_token
            payload = request_json("GET", cal_path(calendar_id, "/events"), token=access_token(), params=params)
            events.extend(payload.get("items", []))
            page_token = payload.get("nextPageToken") or ""
            new_sync_token = payload.get("nextSyncToken") or new_sync_token
            if not page_token:
                break
    except HTTPStatusError as error:
        if error.status == 410:
            print("SYNC_TOKEN_EXPIRED_FULL_SYNC_REQUIRED", file=sys.stderr)
            raise SystemExit(2)
        raise
    print_json({"events": events, "nextSyncToken": new_sync_token})
