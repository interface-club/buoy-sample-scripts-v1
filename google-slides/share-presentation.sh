#!/usr/bin/env bash

: "${ACCESS_TOKEN:?ACCESS_TOKEN is required}"
: "${PRESENTATION_ID:?PRESENTATION_ID is required}"
: "${EMAIL:?EMAIL is required}"
ROLE="${ROLE:-reader}"

BODY="$(jq -n --arg email "$EMAIL" --arg role "$ROLE" '{
  type: "user",
  role: $role,
  emailAddress: $email
}')"

curl -sS -X POST \
  -H "Authorization: Bearer $ACCESS_TOKEN" \
  -H "Content-Type: application/json" \
  --data "$BODY" \
  "https://www.googleapis.com/drive/v3/files/$PRESENTATION_ID/permissions?supportsAllDrives=true&sendNotificationEmail=true&fields=id,type,role,emailAddress" \
  | jq .
