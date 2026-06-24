#!/usr/bin/env bash

: "${ACCESS_TOKEN:?ACCESS_TOKEN is required}"
: "${FILE_ID:?FILE_ID is required}"

curl -sS -X DELETE \
  -H "Authorization: Bearer $ACCESS_TOKEN" \
  "https://www.googleapis.com/drive/v3/files/$FILE_ID?supportsAllDrives=true" \
  -w "\nHTTP %{http_code}\n"
