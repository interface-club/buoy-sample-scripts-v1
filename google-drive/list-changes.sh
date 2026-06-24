#!/usr/bin/env bash

: "${ACCESS_TOKEN:?ACCESS_TOKEN is required}"
: "${PAGE_TOKEN:?PAGE_TOKEN is required}"

curl -sS \
  -H "Authorization: Bearer $ACCESS_TOKEN" \
  "https://www.googleapis.com/drive/v3/changes?pageToken=$PAGE_TOKEN&supportsAllDrives=true&includeItemsFromAllDrives=true&fields=nextPageToken,newStartPageToken,changes(fileId,removed,time,file(id,name,mimeType,trashed,modifiedTime,webViewLink))" \
| jq .
