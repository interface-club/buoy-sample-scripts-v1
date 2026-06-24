#!/usr/bin/env bash

: "${ACCESS_TOKEN:?ACCESS_TOKEN is required}"
: "${FILE_ID:?FILE_ID is required}"

jq -n '{trashed:true}' \
| curl -sS -X PATCH \
  -H "Authorization: Bearer $ACCESS_TOKEN" \
  -H "Content-Type: application/json" \
  -d @- \
  "https://www.googleapis.com/drive/v3/files/$FILE_ID?supportsAllDrives=true&fields=id,name,trashed" \
| jq .
