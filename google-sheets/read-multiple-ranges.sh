#!/usr/bin/env bash

: "${ACCESS_TOKEN:?ACCESS_TOKEN is required}"
: "${SPREADSHEET_ID:?SPREADSHEET_ID is required}"
: "${RANGES_JSON:?RANGES_JSON is required}"

args=()
while IFS= read -r range; do
  args+=(--data-urlencode "ranges=$range")
done < <(jq -r '.[]' <<<"$RANGES_JSON")

curl -sS -G "https://sheets.googleapis.com/v4/spreadsheets/$SPREADSHEET_ID/values:batchGet" \
  -H "Authorization: Bearer $ACCESS_TOKEN" \
  "${args[@]}" \
  --data-urlencode "majorDimension=ROWS" \
  --data-urlencode "valueRenderOption=FORMATTED_VALUE" \
| jq '.valueRanges[] | {range, values}'
