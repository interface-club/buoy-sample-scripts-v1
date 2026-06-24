#!/usr/bin/env bash

: "${ACCESS_TOKEN:?ACCESS_TOKEN is required}"
: "${FILE_ID:?FILE_ID is required}"
: "${MIME:?MIME is required}"
: "${OUT:?OUT is required}"

curl -L -sS \
  -H "Authorization: Bearer $ACCESS_TOKEN" \
  "https://www.googleapis.com/drive/v3/files/$FILE_ID/export?mimeType=$(printf '%s' "$MIME" | jq -sRr @uri)" \
  -o "$OUT"
