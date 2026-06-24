#!/usr/bin/env bash

: "${ACCESS_TOKEN:?ACCESS_TOKEN is required}"
: "${LOCAL_PATH:?LOCAL_PATH is required}"
: "${NAME:?NAME is required}"
: "${MIME:?MIME is required}"
PARENT_ID="${PARENT_ID:-root}"
BOUNDARY="buoy_boundary_$(date +%s)"

{
  printf -- "--%s\r\nContent-Type: application/json; charset=UTF-8\r\n\r\n" "$BOUNDARY"
  jq -n --arg name "$NAME" --arg parent "$PARENT_ID" '{name:$name,parents:[$parent]}'
  printf "\r\n--%s\r\nContent-Type: %s\r\n\r\n" "$BOUNDARY" "$MIME"
  cat "$LOCAL_PATH"
  printf "\r\n--%s--\r\n" "$BOUNDARY"
} | curl -sS -X POST \
  -H "Authorization: Bearer $ACCESS_TOKEN" \
  -H "Content-Type: multipart/related; boundary=$BOUNDARY" \
  --data-binary @- \
  "https://www.googleapis.com/upload/drive/v3/files?uploadType=multipart&supportsAllDrives=true&fields=id,name,webViewLink" \
| jq .
