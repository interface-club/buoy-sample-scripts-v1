#!/usr/bin/env bash

: "${ACCESS_TOKEN:?ACCESS_TOKEN is required}"
MIN_ACCESS_ROLE="${MIN_ACCESS_ROLE:-reader}"
PAGE_TOKEN=""

while :; do
  response=$(curl -sS --get \
    -H "Authorization: Bearer $ACCESS_TOKEN" \
    --data-urlencode "maxResults=250" \
    --data-urlencode "minAccessRole=$MIN_ACCESS_ROLE" \
    ${PAGE_TOKEN:+--data-urlencode "pageToken=$PAGE_TOKEN"} \
    "https://www.googleapis.com/calendar/v3/users/me/calendarList")

  printf '%s\n' "$response" | jq -r '
    .items[] |
    {
      id,
      summary,
      primary: (.primary // false),
      accessRole,
      timeZone,
      selected: (.selected // false)
    }'

  PAGE_TOKEN=$(printf '%s\n' "$response" | jq -r '.nextPageToken // empty')
  [ -z "$PAGE_TOKEN" ] && break
done
