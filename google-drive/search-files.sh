#!/usr/bin/env bash

: "${ACCESS_TOKEN:?ACCESS_TOKEN is required}"
QUERY="${QUERY:-name contains 'invoice' and trashed=false}"
PAGE_SIZE="${PAGE_SIZE:-50}"
FIELDS="nextPageToken,incompleteSearch,files(id,name,mimeType,parents,driveId,modifiedTime,size,webViewLink,capabilities/canDownload)"
PAGE_TOKEN=""

while :; do
  Q_ENC="$(printf '%s' "$QUERY" | jq -sRr @uri)"
  F_ENC="$(printf '%s' "$FIELDS" | jq -sRr @uri)"
  URL="https://www.googleapis.com/drive/v3/files?q=$Q_ENC&pageSize=$PAGE_SIZE&fields=$F_ENC&supportsAllDrives=true&includeItemsFromAllDrives=true"
  [ -n "$PAGE_TOKEN" ] && URL="$URL&pageToken=$(printf '%s' "$PAGE_TOKEN" | jq -sRr @uri)"
  RESP="$(curl -sS -H "Authorization: Bearer $ACCESS_TOKEN" "$URL")"
  echo "$RESP" | jq -r '.files[] | [.id,.name,.mimeType,.modifiedTime,.webViewLink] | @tsv'
  PAGE_TOKEN="$(echo "$RESP" | jq -r '.nextPageToken // empty')"
  [ -z "$PAGE_TOKEN" ] && break
done
