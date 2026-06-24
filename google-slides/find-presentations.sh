#!/usr/bin/env bash

: "${ACCESS_TOKEN:?ACCESS_TOKEN is required}"
: "${QUERY_TEXT:?QUERY_TEXT is required}"
Q="mimeType='application/vnd.google-apps.presentation' and trashed=false and name contains '${QUERY_TEXT}'"
export Q
ENC_Q="$(python3 - <<'PY'
import os, urllib.parse
print(urllib.parse.quote(os.environ["Q"]))
PY
)"
curl -sS \
  -H "Authorization: Bearer $ACCESS_TOKEN" \
  "https://www.googleapis.com/drive/v3/files?q=$ENC_Q&pageSize=20&supportsAllDrives=true&includeItemsFromAllDrives=true&fields=nextPageToken,files(id,name,webViewLink,modifiedTime,owners(displayName,emailAddress),driveId)" \
  | jq .
