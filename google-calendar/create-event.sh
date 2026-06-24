#!/usr/bin/env bash

: "${ACCESS_TOKEN:?ACCESS_TOKEN is required}"
CALENDAR_ID="${CALENDAR_ID:-primary}"
CALENDAR_ID_ENC=$(printf '%s' "$CALENDAR_ID" | jq -sRr @uri)
: "${SUMMARY:?SUMMARY is required}"
: "${START:?START is required}"
: "${END:?END is required}"
TIME_ZONE="${TIME_ZONE:-UTC}"
LOCATION="${LOCATION:-}"
DESCRIPTION="${DESCRIPTION:-}"
SEND_UPDATES="${SEND_UPDATES:-all}"
ATTENDEES_JSON="${ATTENDEES_JSON:-[]}"

body=$(jq -n \
  --arg summary "$SUMMARY" \
  --arg start "$START" \
  --arg end "$END" \
  --arg timeZone "$TIME_ZONE" \
  --arg location "$LOCATION" \
  --arg description "$DESCRIPTION" \
  --argjson attendees "$ATTENDEES_JSON" \
  '{
    summary: $summary,
    location: $location,
    description: $description,
    start: {dateTime: $start, timeZone: $timeZone},
    end: {dateTime: $end, timeZone: $timeZone},
    attendees: $attendees,
    reminders: {useDefault: true}
  }')

curl -sS -X POST \
  -H "Authorization: Bearer $ACCESS_TOKEN" \
  -H "Content-Type: application/json" \
  --data "$body" \
  "https://www.googleapis.com/calendar/v3/calendars/$CALENDAR_ID_ENC/events?sendUpdates=$SEND_UPDATES" |
jq '{id, summary, start, end, attendees, htmlLink, etag}'
