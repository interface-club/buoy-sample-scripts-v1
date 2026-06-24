#!/usr/bin/env bash

: "${ACCESS_TOKEN:?ACCESS_TOKEN is required}"
CALENDAR_ID="${CALENDAR_ID:-primary}"
: "${EVENT_ID:?EVENT_ID is required}"
CALENDAR_ID_ENC=$(printf '%s' "$CALENDAR_ID" | jq -sRr @uri)
EVENT_ID_ENC=$(printf '%s' "$EVENT_ID" | jq -sRr @uri)

curl -sS \
  -H "Authorization: Bearer $ACCESS_TOKEN" \
  "https://www.googleapis.com/calendar/v3/calendars/$CALENDAR_ID_ENC/events/$EVENT_ID_ENC" |
jq '{
  id, etag, status, summary, description, location,
  start, end, recurrence, recurringEventId, originalStartTime,
  organizer, creator, attendees, reminders, conferenceData, htmlLink
}'
