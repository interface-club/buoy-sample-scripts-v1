#!/usr/bin/env bash

: "${ACCESS_TOKEN:?ACCESS_TOKEN is required}"
: "${QUERY:?QUERY is required}"
: "${NEXT_PAGE_TOKEN:?NEXT_PAGE_TOKEN is required}"

curl -sS -G "https://www.googleapis.com/drive/v3/files" \
  -H "Authorization: Bearer $ACCESS_TOKEN" \
  --data-urlencode "q=$QUERY" \
  --data-urlencode "pageToken=$NEXT_PAGE_TOKEN" \
  --data-urlencode "pageSize=20" \
  --data-urlencode "supportsAllDrives=true" \
  --data-urlencode "includeItemsFromAllDrives=true" \
  --data-urlencode "fields=nextPageToken,files(id,name,webViewLink,modifiedTime,owners(emailAddress),mimeType)"
