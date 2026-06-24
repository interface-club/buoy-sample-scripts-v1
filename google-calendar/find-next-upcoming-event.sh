#!/usr/bin/env bash

: "${ACCESS_TOKEN:?ACCESS_TOKEN is required}"
ACCESS_TOKEN="${ACCESS_TOKEN:?access token required}"
TIME_MIN="${TIME_MIN:-$(date -u +"%Y-%m-%dT%H:%M:%SZ")}"
TIME_MAX="${TIME_MAX:-}"
EVENTS_PER_CALENDAR="${EVENTS_PER_CALENDAR:-10}"
CALENDAR_IDS_JSON="${CALENDAR_IDS_JSON:-}"
INCLUDE_ALL_DAY="${INCLUDE_ALL_DAY:-true}"
export ACCESS_TOKEN TIME_MIN TIME_MAX EVENTS_PER_CALENDAR CALENDAR_IDS_JSON INCLUDE_ALL_DAY

python3 <<'PY'
import json
import os
import sys
import urllib.error
import urllib.parse
import urllib.request
from datetime import date, datetime, time, timedelta, timezone

try:
    from zoneinfo import ZoneInfo
except Exception:
    ZoneInfo = None

BASE_URL = "https://www.googleapis.com/calendar/v3"
ACCESS_TOKEN = os.environ["ACCESS_TOKEN"]


def parse_rfc3339(value):
    normalized = value[:-1] + "+00:00" if value.endswith("Z") else value
    parsed = datetime.fromisoformat(normalized)
    if parsed.tzinfo is None:
        parsed = parsed.replace(tzinfo=timezone.utc)
    return parsed.astimezone(timezone.utc)


def iso_z(value):
    return value.astimezone(timezone.utc).isoformat().replace("+00:00", "Z")


def request_json(path, params=None):
    query = urllib.parse.urlencode(params or {})
    url = f"{BASE_URL}{path}{'?' + query if query else ''}"
    request = urllib.request.Request(
        url,
        headers={"Authorization": f"Bearer {ACCESS_TOKEN}"},
    )
    try:
        with urllib.request.urlopen(request) as response:
            return json.load(response)
    except urllib.error.HTTPError as error:
        sys.stderr.write(error.read().decode("utf-8", errors="replace"))
        raise


def calendar_timezone(calendar):
    name = calendar.get("timeZone") or "UTC"
    if ZoneInfo is None:
        return timezone.utc
    try:
        return ZoneInfo(name)
    except Exception:
        return timezone.utc


def event_start_instant(event, calendar, include_all_day):
    start = event.get("start") or {}
    if start.get("dateTime"):
        return parse_rfc3339(start["dateTime"]), False
    if start.get("date"):
        if not include_all_day:
            return None, True
        local_date = date.fromisoformat(start["date"])
        return datetime.combine(local_date, time.min, calendar_timezone(calendar)).astimezone(
            timezone.utc
        ), True
    return None, False


def calendar_path(calendar_id, suffix=""):
    encoded = urllib.parse.quote(calendar_id, safe="")
    return f"/calendars/{encoded}{suffix}"


time_min = os.environ["TIME_MIN"]
lower_bound = parse_rfc3339(time_min)
time_max = os.environ.get("TIME_MAX") or iso_z(lower_bound + timedelta(days=30))
events_per_calendar = max(2, int(os.environ.get("EVENTS_PER_CALENDAR") or "10"))
include_all_day = os.environ.get("INCLUDE_ALL_DAY", "true").lower() != "false"
calendar_ids_json = os.environ.get("CALENDAR_IDS_JSON", "").strip()

if calendar_ids_json:
    calendar_ids = json.loads(calendar_ids_json)
    calendars = [
        request_json(calendar_path(calendar_id), {"fields": "id,summary,timeZone,backgroundColor"})
        for calendar_id in calendar_ids
    ]
else:
    all_calendars = []
    page_token = None
    while True:
        params = {
            "maxResults": 250,
            "minAccessRole": "reader",
            "fields": "items(id,summary,primary,selected,hidden,timeZone,backgroundColor),nextPageToken",
        }
        if page_token:
            params["pageToken"] = page_token
        payload = request_json("/users/me/calendarList", params)
        all_calendars.extend(
            calendar for calendar in payload.get("items", []) if not calendar.get("hidden", False)
        )
        page_token = payload.get("nextPageToken")
        if not page_token:
            break
    calendars = [
        calendar
        for calendar in all_calendars
        if calendar.get("primary", False) or calendar.get("selected", False)
    ] or all_calendars

candidates = []
for calendar in calendars:
    payload = request_json(
        calendar_path(calendar["id"], "/events"),
        {
            "timeMin": time_min,
            "timeMax": time_max,
            "singleEvents": "true",
            "orderBy": "startTime",
            "maxResults": events_per_calendar,
            "fields": "items(id,status,summary,start,end,location,htmlLink,attendees(email,responseStatus),organizer(email,displayName),creator(email,displayName))",
        },
    )
    for event in payload.get("items", []):
        if event.get("status") == "cancelled":
            continue
        start_instant, is_all_day = event_start_instant(event, calendar, include_all_day)
        if start_instant is None or start_instant < lower_bound:
            continue
        candidates.append(
            {
                "startInstant": start_instant,
                "isAllDay": is_all_day,
                "calendar": calendar,
                "event": event,
            }
        )

candidates.sort(key=lambda item: item["startInstant"])

if not candidates:
    print("null")
else:
    selected = candidates[0]
    event = selected["event"]
    calendar = selected["calendar"]
    print(
        json.dumps(
            {
                "calendarID": calendar["id"],
                "calendarSummary": calendar.get("summary"),
                "calendarColorHex": calendar.get("backgroundColor"),
                "id": event["id"],
                "summary": event.get("summary", "(No title)"),
                "startInstant": iso_z(selected["startInstant"]),
                "isAllDay": selected["isAllDay"],
                "start": event.get("start"),
                "end": event.get("end"),
                "location": event.get("location"),
                "htmlLink": event.get("htmlLink"),
                "organizer": event.get("organizer"),
                "attendees": event.get("attendees", []),
            },
            indent=2,
        )
    )
PY
