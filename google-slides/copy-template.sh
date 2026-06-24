#!/usr/bin/env bash

: "${ACCESS_TOKEN:?ACCESS_TOKEN is required}"
: "${TEMPLATE_ID:?TEMPLATE_ID is required}"
: "${NEW_TITLE:?NEW_TITLE is required}"
DEST_FOLDER_ID="${DEST_FOLDER_ID:-}"

BODY="$(jq -n --arg name "$NEW_TITLE" --arg parent "$DEST_FOLDER_ID" '
  {name:$name}
  | if $parent == "OPTIONAL_FOLDER_ID" or $parent == "" then .
    else . + {parents:[$parent]}
    end
')"

curl -sS -X POST \
  -H "Authorization: Bearer $ACCESS_TOKEN" \
  -H "Content-Type: application/json" \
  --data "$BODY" \
  "https://www.googleapis.com/drive/v3/files/$TEMPLATE_ID/copy?supportsAllDrives=true&fields=id,name,webViewLink" \
  | jq .
