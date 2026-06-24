#!/usr/bin/env bash

: "${ACCESS_TOKEN:?ACCESS_TOKEN is required}"
: "${NEW_TITLE:?NEW_TITLE is required}"
: "${TEMPLATE_ID:?TEMPLATE_ID is required}"
COPY_JSON="$(curl -sS -X POST \
  -H "Authorization: Bearer $ACCESS_TOKEN" \
  -H "Content-Type: application/json" \
  "https://www.googleapis.com/drive/v3/files/$TEMPLATE_ID/copy?supportsAllDrives=true&fields=id,name,webViewLink" \
  -d "$(jq -n --arg name "$NEW_TITLE" '{name:$name}')")"

NEW_DOCUMENT_ID="$(printf '%s' "$COPY_JSON" | jq -r '.id')"
printf '%s\n' "$COPY_JSON" | jq .
