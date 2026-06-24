#!/usr/bin/env bash

: "${ACCESS_TOKEN:?ACCESS_TOKEN is required}"
: "${DOCUMENT_ID:?DOCUMENT_ID is required}"
MIME_TYPE="${MIME_TYPE:-application/pdf}"
OUT="${OUT:-document.pdf}"
export DOCUMENT_ID MIME_TYPE

python3 - <<'PY' > /tmp/google_docs_export_url
import os, urllib.parse
doc = os.environ["DOCUMENT_ID"]
mime = os.environ["MIME_TYPE"]
print("https://www.googleapis.com/drive/v3/files/%s/export?%s" % (
  urllib.parse.quote(doc, safe=""),
  urllib.parse.urlencode({"mimeType": mime})
))
PY

curl -sS -L \
  -H "Authorization: Bearer $ACCESS_TOKEN" \
  "$(cat /tmp/google_docs_export_url)" \
  -o "$OUT"
