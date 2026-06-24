#!/usr/bin/env bash

: "${ACCESS_TOKEN:?ACCESS_TOKEN is required}"
CALENDAR_ID="${CALENDAR_ID:-primary}"
: "${EVENT_ID:?EVENT_ID is required}"
CALENDAR_ID_ENC=$(printf '%s' "$CALENDAR_ID" | jq -sRr @uri)
EVENT_ID_ENC=$(printf '%s' "$EVENT_ID" | jq -sRr @uri)
SEND_UPDATES="${SEND_UPDATES:-all}"
ADD_EMAILS_JSON="${ADD_EMAILS_JSON:-[]}"
REMOVE_EMAILS_JSON="${REMOVE_EMAILS_JSON:-[]}"

current=$(curl -sS \
  -H "Authorization: Bearer $ACCESS_TOKEN" \
  "https://www.googleapis.com/calendar/v3/calendars/$CALENDAR_ID_ENC/events/$EVENT_ID_ENC")

etag=$(printf '%s' "$current" | jq -r '.etag')

updated=$(printf '%s' "$current" | jq \
  --argjson add "$ADD_EMAILS_JSON" \
  --argjson remove "$REMOVE_EMAILS_JSON" '
  .attendees = (
    ((.attendees // []) | map(select(.email as $e | ($remove | index($e) | not))))
    + ($add | map({email: .}))
    | unique_by(.email)
  )
')

printf '%s\n' "$updated" | jq '{id, summary, start, end, attendees}'

curl -sS -X PUT \
  -H "Authorization: Bearer $ACCESS_TOKEN" \
  -H "Content-Type: application/json" \
  -H "If-Match: $etag" \
  --data "$updated" \
  "https://www.googleapis.com/calendar/v3/calendars/$CALENDAR_ID_ENC/events/$EVENT_ID_ENC?sendUpdates=$SEND_UPDATES" |
jq '{id, summary, attendees, htmlLink, etag}'
