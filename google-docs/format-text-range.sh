#!/usr/bin/env bash

: "${ACCESS_TOKEN:?ACCESS_TOKEN is required}"
: "${END_INDEX:?END_INDEX is required}"
: "${START_INDEX:?START_INDEX is required}"
: "${TAB_ID:?TAB_ID is required}"
: "${DOCUMENT_ID:?DOCUMENT_ID is required}"
DOC_JSON="$(curl -sS \
  -H "Authorization: Bearer $ACCESS_TOKEN" \
  "https://docs.googleapis.com/v1/documents/$DOCUMENT_ID?includeTabsContent=true&suggestionsViewMode=SUGGESTIONS_INLINE")"
REVISION_ID="$(printf '%s' "$DOC_JSON" | jq -r '.revisionId')"

jq -n \
  --arg tab_id "$TAB_ID" \
  --argjson start "$START_INDEX" \
  --argjson end "$END_INDEX" \
  --arg rev "$REVISION_ID" '{
    requests: [{
      updateTextStyle: {
        range: {tabId: $tab_id, startIndex: $start, endIndex: $end},
        textStyle: {bold: true},
        fields: "bold"
      }
    }],
    writeControl: {requiredRevisionId: $rev}
  }' > /tmp/docs_format.json

curl -sS -X POST \
  -H "Authorization: Bearer $ACCESS_TOKEN" \
  -H "Content-Type: application/json" \
  "https://docs.googleapis.com/v1/documents/$DOCUMENT_ID:batchUpdate" \
  --data @/tmp/docs_format.json \
  | jq '{documentId,writeControl}'
