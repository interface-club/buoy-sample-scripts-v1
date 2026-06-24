#!/usr/bin/env bash

: "${ACCESS_TOKEN:?ACCESS_TOKEN is required}"
CALENDAR_ID="${CALENDAR_ID:-primary}"
: "${EVENT_ID:?EVENT_ID is required}"
CALENDAR_ID_ENC=$(printf '%s' "$CALENDAR_ID" | jq -sRr @uri)
EVENT_ID_ENC=$(printf '%s' "$EVENT_ID" | jq -sRr @uri)
SEND_UPDATES="${SEND_UPDATES:-all}"

current=$(curl -sS \
  -H "Authorization: Bearer $ACCESS_TOKEN" \
  "https://www.googleapis.com/calendar/v3/calendars/$CALENDAR_ID_ENC/events/$EVENT_ID_ENC")

etag=$(printf '%s' "$current" | jq -r '.etag')
printf '%s\n' "$current" | jq '{id, summary, start, end, attendees, htmlLink, etag}'

patch=$(jq -n \
  --arg summary "${NEW_SUMMARY:-}" \
  --arg location "${NEW_LOCATION:-}" \
  '{
    summary: (if $summary == "" then empty else $summary end),
    location: (if $location == "" then empty else $location end)
  }')

curl -sS -X PATCH \
  -H "Authorization: Bearer $ACCESS_TOKEN" \
  -H "Content-Type: application/json" \
  -H "If-Match: $etag" \
  --data "$patch" \
  "https://www.googleapis.com/calendar/v3/calendars/$CALENDAR_ID_ENC/events/$EVENT_ID_ENC?sendUpdates=$SEND_UPDATES" |
jq '{id, summary, start, end, location, attendees, htmlLink, etag}'
