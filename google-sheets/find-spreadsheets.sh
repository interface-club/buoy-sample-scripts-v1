#!/usr/bin/env bash

: "${ACCESS_TOKEN:?ACCESS_TOKEN is required}"
QUERY="${QUERY:-mimeType = 'application/vnd.google-apps.spreadsheet' and trashed = false}"

curl -sS -G "https://www.googleapis.com/drive/v3/files" \
  -H "Authorization: Bearer $ACCESS_TOKEN" \
  --data-urlencode "q=$QUERY" \
  --data-urlencode "pageSize=20" \
  --data-urlencode "supportsAllDrives=true" \
  --data-urlencode "includeItemsFromAllDrives=true" \
  --data-urlencode "fields=nextPageToken,files(id,name,webViewLink,modifiedTime,owners(emailAddress),mimeType)" \
| jq '.files[]'
