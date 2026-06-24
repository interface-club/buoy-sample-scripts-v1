#!/usr/bin/env bash

: "${ACCESS_TOKEN:?ACCESS_TOKEN is required}"
: "${DRIVE_ID:?DRIVE_ID is required}"
QUERY="${QUERY:-trashed=false}"
Q_ENC="$(printf '%s' "$QUERY" | jq -sRr @uri)"

curl -sS \
  -H "Authorization: Bearer $ACCESS_TOKEN" \
  "https://www.googleapis.com/drive/v3/files?corpora=drive&driveId=$DRIVE_ID&includeItemsFromAllDrives=true&supportsAllDrives=true&q=$Q_ENC&pageSize=100&fields=nextPageToken,incompleteSearch,files(id,name,mimeType,parents,driveId,modifiedTime,webViewLink)" \
| jq .
