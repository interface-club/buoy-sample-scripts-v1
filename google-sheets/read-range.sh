#!/usr/bin/env bash

: "${ACCESS_TOKEN:?ACCESS_TOKEN is required}"
: "${SPREADSHEET_ID:?SPREADSHEET_ID is required}"
: "${RANGE:?RANGE is required}"

curl -sS -G "https://sheets.googleapis.com/v4/spreadsheets/$SPREADSHEET_ID/values/$RANGE" \
  -H "Authorization: Bearer $ACCESS_TOKEN" \
  --data-urlencode "majorDimension=ROWS" \
  --data-urlencode "valueRenderOption=FORMATTED_VALUE" \
| jq .
