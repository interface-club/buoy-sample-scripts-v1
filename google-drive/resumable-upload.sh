#!/usr/bin/env bash

: "${ACCESS_TOKEN:?ACCESS_TOKEN is required}"
: "${LOCAL_PATH:?LOCAL_PATH is required}"
: "${NAME:?NAME is required}"
: "${MIME:?MIME is required}"
PARENT_ID="${PARENT_ID:-root}"
SIZE="$(wc -c < "$LOCAL_PATH" | tr -d ' ')"

SESSION_URL="$(
  jq -n --arg name "$NAME" --arg parent "$PARENT_ID" '{name:$name,parents:[$parent]}' \
  | curl -sS -D - -o /dev/null -X POST \
      -H "Authorization: Bearer $ACCESS_TOKEN" \
      -H "Content-Type: application/json; charset=UTF-8" \
      -H "X-Upload-Content-Type: $MIME" \
      -H "X-Upload-Content-Length: $SIZE" \
      -d @- \
      "https://www.googleapis.com/upload/drive/v3/files?uploadType=resumable&supportsAllDrives=true&fields=id,name,webViewLink" \
  | awk 'BEGIN{IGNORECASE=1} /^location:/ {sub(/\r$/,"",$2); print $2}'
)"

curl -sS -X PUT \
  -H "Content-Type: $MIME" \
  -H "Content-Length: $SIZE" \
  --data-binary @"$LOCAL_PATH" \
  "$SESSION_URL" \
| jq .
