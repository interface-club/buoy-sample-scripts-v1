#!/usr/bin/env bash

: "${ACCESS_TOKEN:?ACCESS_TOKEN is required}"
: "${SPREADSHEET_ID:?SPREADSHEET_ID is required}"

curl -sS -G "https://www.googleapis.com/drive/v3/files/$SPREADSHEET_ID" \
  -H "Authorization: Bearer $ACCESS_TOKEN" \
  --data-urlencode "supportsAllDrives=true" \
  --data-urlencode "fields=id,name,mimeType,webViewLink,owners(emailAddress),capabilities(canShare)" \
| jq .
