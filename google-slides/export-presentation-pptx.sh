#!/usr/bin/env bash

: "${ACCESS_TOKEN:?ACCESS_TOKEN is required}"
: "${PRESENTATION_ID:?PRESENTATION_ID is required}"
: "${OUT:?OUT is required}"
MIME='application/vnd.openxmlformats-officedocument.presentationml.presentation'
export MIME
ENC_MIME="$(python3 - <<'PY'
import os, urllib.parse
print(urllib.parse.quote(os.environ["MIME"]))
PY
)"
curl -L -sS \
  -H "Authorization: Bearer $ACCESS_TOKEN" \
  "https://www.googleapis.com/drive/v3/files/$PRESENTATION_ID/export?mimeType=$ENC_MIME" \
  -o "$OUT"
