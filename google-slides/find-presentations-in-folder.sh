#!/usr/bin/env bash

: "${ACCESS_TOKEN:?ACCESS_TOKEN is required}"
: "${FOLDER_ID:?FOLDER_ID is required}"
Q="'${FOLDER_ID}' in parents and mimeType='application/vnd.google-apps.presentation' and trashed=false"
export Q
ENC_Q="$(python3 - <<'PY'
import os, urllib.parse
print(urllib.parse.quote(os.environ["Q"]))
PY
)"
curl -sS -H "Authorization: Bearer $ACCESS_TOKEN" \
  "https://www.googleapis.com/drive/v3/files?q=$ENC_Q&pageSize=100&supportsAllDrives=true&includeItemsFromAllDrives=true&fields=nextPageToken,files(id,name,webViewLink,modifiedTime)" \
  | jq .
