#!/usr/bin/env bash

: "${ACCESS_TOKEN:?ACCESS_TOKEN is required}"
CALENDAR_ID="${CALENDAR_ID:-primary}"
CALENDAR_ID_ENC=$(printf '%s' "$CALENDAR_ID" | jq -sRr @uri)
: "${TIME_MIN:?TIME_MIN is required}"
: "${TIME_MAX:?TIME_MAX is required}"
QUERY="${QUERY:-}"
PAGE_TOKEN=""

calendar_metadata=$(curl -sS \
  -H "Authorization: Bearer $ACCESS_TOKEN" \
  "https://www.googleapis.com/calendar/v3/users/me/calendarList/$CALENDAR_ID_ENC?fields=id,summary,backgroundColor")
calendar_color_hex=$(printf '%s\n' "$calendar_metadata" | jq -r '.backgroundColor // empty')

event_colors=$(curl -sS \
  -H "Authorization: Bearer $ACCESS_TOKEN" \
  "https://www.googleapis.com/calendar/v3/colors?fields=event" |
  jq -c '.event // {}')

while :; do
  response=$(curl -sS --get \
    -H "Authorization: Bearer $ACCESS_TOKEN" \
    --data-urlencode "timeMin=$TIME_MIN" \
    --data-urlencode "timeMax=$TIME_MAX" \
    --data-urlencode "singleEvents=true" \
    --data-urlencode "orderBy=startTime" \
    --data-urlencode "maxResults=250" \
    --data-urlencode "fields=items(id,etag,status,summary,start,end,location,htmlLink,colorId,attendees(email,responseStatus),organizer(email,displayName),creator(email,displayName)),nextPageToken,nextSyncToken" \
    ${QUERY:+--data-urlencode "q=$QUERY"} \
    ${PAGE_TOKEN:+--data-urlencode "pageToken=$PAGE_TOKEN"} \
    "https://www.googleapis.com/calendar/v3/calendars/$CALENDAR_ID_ENC/events")

  printf '%s\n' "$response" | jq -r \
    --arg calendarColorHex "$calendar_color_hex" \
    --argjson eventColors "$event_colors" \
    '.items[] | {
    id, status, summary, start, end, location, htmlLink,
    colorId: (.colorId // null),
    calendarColorHex: (if $calendarColorHex == "" then null else $calendarColorHex end),
    eventColorHex: (
      if .colorId and ($eventColors[.colorId].background? != null) then $eventColors[.colorId].background
      elif $calendarColorHex != "" then $calendarColorHex
      else null
      end
    ),
    attendees: [.attendees[]?.email]
  }'

  PAGE_TOKEN=$(printf '%s\n' "$response" | jq -r '.nextPageToken // empty')
  [ -z "$PAGE_TOKEN" ] && break
done
