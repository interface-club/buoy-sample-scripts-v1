#!/usr/bin/env bash

QUERY='from:alice@example.com newer_than:30d -in:trash'
MAX_TOTAL=200
PAGE_TOKEN=""
SEEN=0

while :; do
  args=(-fsS -G "$BASE/messages"
    -H "Authorization: Bearer $ACCESS_TOKEN"
    --data-urlencode "q=$QUERY"
    --data-urlencode "maxResults=100")
  [ -n "$PAGE_TOKEN" ] && args+=(--data-urlencode "pageToken=$PAGE_TOKEN")

  RESP="$(curl "${args[@]}")"
  echo "$RESP" | jq -r --arg email "$ACCOUNT_EMAIL" \
    '.messages[]? | [.id, .threadId, "https://mail.google.com/mail/?authuser=\($email)#all/\(.id)"] | @tsv'

  COUNT="$(echo "$RESP" | jq '.messages | length // 0')"
  SEEN=$((SEEN + COUNT))
  PAGE_TOKEN="$(echo "$RESP" | jq -r '.nextPageToken // empty')"
  [ -z "$PAGE_TOKEN" ] || [ "$SEEN" -ge "$MAX_TOTAL" ] && break
done
