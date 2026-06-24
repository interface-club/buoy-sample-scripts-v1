#!/usr/bin/env bash

: "${ACCESS_TOKEN:?ACCESS_TOKEN is required}"
: "${FILE_ID:?FILE_ID is required}"
TYPE="${TYPE:-user}"
ROLE="${ROLE:-reader}"
: "${EMAIL:?EMAIL is required}"
SEND_NOTIFICATION="${SEND_NOTIFICATION:-true}"

jq -n --arg type "$TYPE" --arg role "$ROLE" --arg email "$EMAIL" \
  '{type:$type,role:$role,emailAddress:$email}' \
| curl -sS -X POST \
  -H "Authorization: Bearer $ACCESS_TOKEN" \
  -H "Content-Type: application/json" \
  -d @- \
  "https://www.googleapis.com/drive/v3/files/$FILE_ID/permissions?supportsAllDrives=true&sendNotificationEmail=$SEND_NOTIFICATION&fields=id,type,role,emailAddress" \
| jq .
