#!/usr/bin/env bash

: "${ACCESS_TOKEN:?ACCESS_TOKEN is required}"
: "${QUERY:?QUERY is required}"
export QUERY
export PAGE_TOKEN="${PAGE_TOKEN:-}"
python3 - <<'PY' > /tmp/google_docs_search_url
import os, urllib.parse
query = os.environ["QUERY"].replace("\\", "\\\\").replace("'", "\\'")
drive_q = "mimeType = 'application/vnd.google-apps.document' and trashed = false and name contains '%s'" % query
params = {
  "q": drive_q,
  "pageSize": "10",
  "fields": "nextPageToken,incompleteSearch,files(id,name,webViewLink,modifiedTime,owners(emailAddress),capabilities(canEdit,canShare))",
  "supportsAllDrives": "true",
  "includeItemsFromAllDrives": "true",
}
if os.environ.get("PAGE_TOKEN"):
  params["pageToken"] = os.environ["PAGE_TOKEN"]
print("https://www.googleapis.com/drive/v3/files?" + urllib.parse.urlencode(params))
PY

curl -sS -H "Authorization: Bearer $ACCESS_TOKEN" "$(cat /tmp/google_docs_search_url)" \
  | jq '.files[] | {id,name,webViewLink,modifiedTime,owners,capabilities}, empty'
