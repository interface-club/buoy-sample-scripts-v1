#!/usr/bin/env bash

: "${ACCESS_TOKEN:?ACCESS_TOKEN is required}"
: "${SPREADSHEET_ID:?SPREADSHEET_ID is required}"
: "${EMAIL:?EMAIL is required}"

BODY="$(jq -n --arg email "$EMAIL" '{
  type: "user",
  role: "reader",
  emailAddress: $email
}')"

curl -sS -X POST \
  "https://www.googleapis.com/drive/v3/files/$SPREADSHEET_ID/permissions?sendNotificationEmail=true&supportsAllDrives=true&fields=id,type,role,emailAddress" \
  -H "Authorization: Bearer $ACCESS_TOKEN" \
  -H "Content-Type: application/json" \
  --data "$BODY" \
| jq .
