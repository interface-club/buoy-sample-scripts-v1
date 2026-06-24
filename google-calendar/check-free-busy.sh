#!/usr/bin/env bash

: "${ACCESS_TOKEN:?ACCESS_TOKEN is required}"
: "${TIME_MIN:?TIME_MIN is required}"
: "${TIME_MAX:?TIME_MAX is required}"
TIME_ZONE="${TIME_ZONE:-UTC}"
CALENDAR_IDS_JSON="${CALENDAR_IDS_JSON:-["primary"]}"

body=$(jq -n \
  --arg timeMin "$TIME_MIN" \
  --arg timeMax "$TIME_MAX" \
  --arg timeZone "$TIME_ZONE" \
  --argjson ids "$CALENDAR_IDS_JSON" \
  '{
    timeMin: $timeMin,
    timeMax: $timeMax,
    timeZone: $timeZone,
    calendarExpansionMax: 50,
    items: ($ids | map({id: .}))
  }')

curl -sS -X POST \
  -H "Authorization: Bearer $ACCESS_TOKEN" \
  -H "Content-Type: application/json" \
  --data "$body" \
  "https://www.googleapis.com/calendar/v3/freeBusy" |
jq '.calendars'
