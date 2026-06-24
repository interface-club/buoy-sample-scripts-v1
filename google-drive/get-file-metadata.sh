#!/usr/bin/env bash

: "${ACCESS_TOKEN:?ACCESS_TOKEN is required}"
: "${FILE_ID:?FILE_ID is required}"
FIELDS="id,name,mimeType,parents,driveId,owners(displayName,emailAddress),createdTime,modifiedTime,size,trashed,webViewLink,webContentLink,exportLinks,capabilities(canDownload,canEdit,canDelete,canShare)"
curl -sS \
  -H "Authorization: Bearer $ACCESS_TOKEN" \
  "https://www.googleapis.com/drive/v3/files/$FILE_ID?supportsAllDrives=true&fields=$(printf '%s' "$FIELDS" | jq -sRr @uri)" \
| jq .
