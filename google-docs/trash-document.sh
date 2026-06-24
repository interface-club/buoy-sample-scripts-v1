#!/usr/bin/env bash

: "${ACCESS_TOKEN:?ACCESS_TOKEN is required}"
: "${DOCUMENT_ID:?DOCUMENT_ID is required}"
curl -sS -X PATCH \
  -H "Authorization: Bearer $ACCESS_TOKEN" \
  -H "Content-Type: application/json" \
  "https://www.googleapis.com/drive/v3/files/$DOCUMENT_ID?supportsAllDrives=true&fields=id,name,trashed" \
  -d '{"trashed":true}' \
  | jq .
