#!/usr/bin/env bash

: "${ACCESS_TOKEN:?ACCESS_TOKEN is required}"
: "${NAME:?NAME is required}"
PARENT_ID="${PARENT_ID:-root}"

jq -n --arg name "$NAME" --arg parent "$PARENT_ID" \
  '{name:$name,mimeType:"application/vnd.google-apps.folder",parents:[$parent]}' \
| curl -sS -X POST \
  -H "Authorization: Bearer $ACCESS_TOKEN" \
  -H "Content-Type: application/json" \
  -d @- \
  "https://www.googleapis.com/drive/v3/files?supportsAllDrives=true&fields=id,name,webViewLink" \
| jq .
