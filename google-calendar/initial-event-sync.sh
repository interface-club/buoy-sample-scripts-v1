#!/usr/bin/env bash

: "${ACCESS_TOKEN:?ACCESS_TOKEN is required}"
CALENDAR_ID="${CALENDAR_ID:-primary}"
CALENDAR_ID_ENC=$(printf '%s' "$CALENDAR_ID" | jq -sRr @uri)
PAGE_TOKEN=""

while :; do
  response=$(curl -sS --get \
    -H "Authorization: Bearer $ACCESS_TOKEN" \
    --data-urlencode "maxResults=250" \
    --data-urlencode "singleEvents=true" \
    --data-urlencode "showDeleted=true" \
    ${PAGE_TOKEN:+--data-urlencode "pageToken=$PAGE_TOKEN"} \
    "https://www.googleapis.com/calendar/v3/calendars/$CALENDAR_ID_ENC/events")

  printf '%s\n' "$response" | jq -c '.items[]'
  PAGE_TOKEN=$(printf '%s\n' "$response" | jq -r '.nextPageToken // empty')
  SYNC_TOKEN=$(printf '%s\n' "$response" | jq -r '.nextSyncToken // empty')

  [ -z "$PAGE_TOKEN" ] && break
done

printf 'NEXT_SYNC_TOKEN=%s\n' "$SYNC_TOKEN"
