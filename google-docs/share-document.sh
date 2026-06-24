#!/usr/bin/env bash

: "${ACCESS_TOKEN:?ACCESS_TOKEN is required}"
: "${ROLE:?ROLE is required}"
: "${TYPE:?TYPE is required}"
: "${DOCUMENT_ID:?DOCUMENT_ID is required}"
jq -n \
  --arg type "$TYPE" \
  --arg role "$ROLE" \
  --arg email "${EMAIL_ADDRESS:-}" \
  --arg domain "${DOMAIN:-}" '
  {type:$type, role:$role}
  + (if $email != "" then {emailAddress:$email} else {} end)
  + (if $domain != "" then {domain:$domain} else {} end)
' > /tmp/docs_permission.json

curl -sS -X POST \
  -H "Authorization: Bearer $ACCESS_TOKEN" \
  -H "Content-Type: application/json" \
  "https://www.googleapis.com/drive/v3/files/$DOCUMENT_ID/permissions?supportsAllDrives=true&sendNotificationEmail=true&fields=id,type,role,emailAddress,domain" \
  --data @/tmp/docs_permission.json \
  | jq .
