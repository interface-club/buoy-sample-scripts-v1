#!/usr/bin/env bash

: "${ACCESS_TOKEN:?ACCESS_TOKEN is required}"
: "${FILE_ID:?FILE_ID is required}"
: "${NEW_NAME:?NEW_NAME is required}"
PARENT_ID="${PARENT_ID:-root}"

jq -n --arg name "$NEW_NAME" --arg parent "$PARENT_ID" '{name:$name,parents:[$parent]}' \
| curl -sS -X POST \
  -H "Authorization: Bearer $ACCESS_TOKEN" \
  -H "Content-Type: application/json" \
  -d @- \
  "https://www.googleapis.com/drive/v3/files/$FILE_ID/copy?supportsAllDrives=true&fields=id,name,webViewLink" \
| jq .
