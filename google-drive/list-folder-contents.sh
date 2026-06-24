#!/usr/bin/env bash

: "${ACCESS_TOKEN:?ACCESS_TOKEN is required}"
FOLDER_ID="${FOLDER_ID:-root}"
QUERY="'$FOLDER_ID' in parents and trashed=false"
Q_ENC="$(printf '%s' "$QUERY" | jq -sRr @uri)"
curl -sS \
  -H "Authorization: Bearer $ACCESS_TOKEN" \
  "https://www.googleapis.com/drive/v3/files?q=$Q_ENC&pageSize=100&supportsAllDrives=true&includeItemsFromAllDrives=true&fields=nextPageToken,files(id,name,mimeType,modifiedTime,size,webViewLink)" \
| jq -r '.files[] | [.id,.name,.mimeType,.modifiedTime] | @tsv'
