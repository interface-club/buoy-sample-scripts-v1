#!/usr/bin/env bash

: "${ACCESS_TOKEN:?ACCESS_TOKEN is required}"
: "${FILE_ID:?FILE_ID is required}"

curl -sS \
  -H "Authorization: Bearer $ACCESS_TOKEN" \
  "https://www.googleapis.com/drive/v3/files/$FILE_ID/permissions?supportsAllDrives=true&fields=permissions(id,type,role,emailAddress,domain,displayName,allowFileDiscovery,expirationTime,deleted)" \
| jq .
