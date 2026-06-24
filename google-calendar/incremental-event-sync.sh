#!/usr/bin/env bash

: "${ACCESS_TOKEN:?ACCESS_TOKEN is required}"
CALENDAR_ID="${CALENDAR_ID:-primary}"
: "${SYNC_TOKEN:?SYNC_TOKEN is required}"
CALENDAR_ID_ENC=$(printf '%s' "$CALENDAR_ID" | jq -sRr @uri)
PAGE_TOKEN=""

while :; do
  response=$(curl -sS -w '\n%{http_code}' --get \
    -H "Authorization: Bearer $ACCESS_TOKEN" \
    --data-urlencode "maxResults=250" \
    --data-urlencode "singleEvents=true" \
    --data-urlencode "showDeleted=true" \
    --data-urlencode "syncToken=$SYNC_TOKEN" \
    ${PAGE_TOKEN:+--data-urlencode "pageToken=$PAGE_TOKEN"} \
    "https://www.googleapis.com/calendar/v3/calendars/$CALENDAR_ID_ENC/events")

  status=$(printf '%s' "$response" | tail -n1)
  payload=$(printf '%s' "$response" | sed '$d')

  if [ "$status" = "410" ]; then
    printf 'SYNC_TOKEN_EXPIRED_FULL_SYNC_REQUIRED\n' >&2
    exit 2
  fi

  [ "$status" = "200" ] || { printf '%s\n' "$payload" >&2; exit 1; }

  printf '%s\n' "$payload" | jq -c '.items[]'
  PAGE_TOKEN=$(printf '%s\n' "$payload" | jq -r '.nextPageToken // empty')
  NEW_SYNC_TOKEN=$(printf '%s\n' "$payload" | jq -r '.nextSyncToken // empty')

  [ -z "$PAGE_TOKEN" ] && break
done

printf 'NEXT_SYNC_TOKEN=%s\n' "$NEW_SYNC_TOKEN"
