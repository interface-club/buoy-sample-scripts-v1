#!/usr/bin/env bash

: "${ACCESS_TOKEN:?ACCESS_TOKEN is required}"
: "${SPREADSHEET_ID:?SPREADSHEET_ID is required}"
: "${MIME_TYPE:?MIME_TYPE is required}"
: "${OUT:?OUT is required}"

curl -sS -L -G \
  "https://www.googleapis.com/drive/v3/files/$SPREADSHEET_ID/export" \
  -H "Authorization: Bearer $ACCESS_TOKEN" \
  --data-urlencode "mimeType=$MIME_TYPE" \
  --output "$OUT"

ls -lh "$OUT"
