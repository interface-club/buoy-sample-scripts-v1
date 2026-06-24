#!/usr/bin/env bash

: "${ACCESS_TOKEN:?ACCESS_TOKEN is required}"
: "${SPREADSHEET_ID:?SPREADSHEET_ID is required}"

curl -sS -G "https://sheets.googleapis.com/v4/spreadsheets/$SPREADSHEET_ID" \
  -H "Authorization: Bearer $ACCESS_TOKEN" \
  --data-urlencode "includeGridData=false" \
  --data-urlencode "fields=spreadsheetId,properties.title,spreadsheetUrl,sheets(properties(sheetId,title,index,gridProperties(rowCount,columnCount,frozenRowCount,frozenColumnCount)))" \
| jq .
