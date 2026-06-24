#!/usr/bin/env bash

: "${ACCESS_TOKEN:?ACCESS_TOKEN is required}"
: "${PRESENTATION_ID:?PRESENTATION_ID is required}"

BODY='{"type":"anyone","role":"reader","allowFileDiscovery":false}'

curl -sS -X POST \
  -H "Authorization: Bearer $ACCESS_TOKEN" \
  -H "Content-Type: application/json" \
  --data "$BODY" \
  "https://www.googleapis.com/drive/v3/files/$PRESENTATION_ID/permissions?supportsAllDrives=true&fields=id,type,role,allowFileDiscovery" \
  | jq .
