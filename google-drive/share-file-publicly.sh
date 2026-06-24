#!/usr/bin/env bash

: "${ACCESS_TOKEN:?ACCESS_TOKEN is required}"
: "${FILE_ID:?FILE_ID is required}"

jq -n '{type:"anyone",role:"reader",allowFileDiscovery:false}' \
| curl -sS -X POST \
  -H "Authorization: Bearer $ACCESS_TOKEN" \
  -H "Content-Type: application/json" \
  -d @- \
  "https://www.googleapis.com/drive/v3/files/$FILE_ID/permissions?supportsAllDrives=true&fields=id,type,role,allowFileDiscovery" \
| jq .
