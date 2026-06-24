#!/usr/bin/env bash

: "${ACCESS_TOKEN:?ACCESS_TOKEN is required}"
: "${SPREADSHEET_ID:?SPREADSHEET_ID is required}"
: "${SHEET_ID:?SHEET_ID is required}"

BODY="$(jq -n --argjson sheetId "$SHEET_ID" '{
  requests: [
    {
      deleteSheet: {
        sheetId: $sheetId
      }
    }
  ]
}')"

curl -sS -X POST \
  "https://sheets.googleapis.com/v4/spreadsheets/$SPREADSHEET_ID:batchUpdate" \
  -H "Authorization: Bearer $ACCESS_TOKEN" \
  -H "Content-Type: application/json" \
  --data "$BODY" \
| jq .
