#!/usr/bin/env bash

: "${ACCESS_TOKEN:?ACCESS_TOKEN is required}"
: "${FILE_ID:?FILE_ID is required}"
: "${OLD_PARENT_ID:?OLD_PARENT_ID is required}"
: "${NEW_PARENT_ID:?NEW_PARENT_ID is required}"

curl -sS -X PATCH \
  -H "Authorization: Bearer $ACCESS_TOKEN" \
  "https://www.googleapis.com/drive/v3/files/$FILE_ID?addParents=$NEW_PARENT_ID&removeParents=$OLD_PARENT_ID&supportsAllDrives=true&fields=id,name,parents,driveId,webViewLink" \
| jq .
