#!/usr/bin/env bash

: "${ACCESS_TOKEN:?ACCESS_TOKEN is required}"
: "${SPREADSHEET_ID:?SPREADSHEET_ID is required}"
: "${RANGE:?RANGE is required}"

: "${BODY_JSON:?BODY_JSON is required}"

curl -sS -X PUT \
  "https://sheets.googleapis.com/v4/spreadsheets/$SPREADSHEET_ID/values/$RANGE?valueInputOption=USER_ENTERED&includeValuesInResponse=true" \
  -H "Authorization: Bearer $ACCESS_TOKEN" \
  -H "Content-Type: application/json" \
  --data "$BODY_JSON" \
| jq .
