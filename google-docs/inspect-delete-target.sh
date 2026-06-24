#!/usr/bin/env bash

: "${ACCESS_TOKEN:?ACCESS_TOKEN is required}"
: "${DOCUMENT_ID:?DOCUMENT_ID is required}"
curl -sS \
  -H "Authorization: Bearer $ACCESS_TOKEN" \
  "https://www.googleapis.com/drive/v3/files/$DOCUMENT_ID?fields=id,name,webViewLink,ownedByMe,owners(emailAddress),trashed,capabilities(canTrash,canDelete)&supportsAllDrives=true" \
  | jq .
