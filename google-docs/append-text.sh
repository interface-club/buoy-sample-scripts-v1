#!/usr/bin/env bash

: "${ACCESS_TOKEN:?ACCESS_TOKEN is required}"
: "${TEXT:?TEXT is required}"
: "${DOCUMENT_ID:?DOCUMENT_ID is required}"
DOC_JSON="$(curl -sS \
  -H "Authorization: Bearer $ACCESS_TOKEN" \
  "https://docs.googleapis.com/v1/documents/$DOCUMENT_ID?includeTabsContent=true&suggestionsViewMode=SUGGESTIONS_INLINE")"

REVISION_ID="$(printf '%s' "$DOC_JSON" | jq -r '.revisionId')"
TAB_ID="${TAB_ID:-$(printf '%s' "$DOC_JSON" | jq -r '.tabs[0].tabProperties.tabId')}"

jq -n --arg text "$TEXT" --arg tab_id "$TAB_ID" --arg rev "$REVISION_ID" '{
  requests: [
    {insertText: {text: $text, endOfSegmentLocation: {tabId: $tab_id}}}
  ],
  writeControl: {requiredRevisionId: $rev}
}' > /tmp/docs_append.json

curl -sS -X POST \
  -H "Authorization: Bearer $ACCESS_TOKEN" \
  -H "Content-Type: application/json" \
  "https://docs.googleapis.com/v1/documents/$DOCUMENT_ID:batchUpdate" \
  --data @/tmp/docs_append.json \
  | jq '{documentId,writeControl}'
