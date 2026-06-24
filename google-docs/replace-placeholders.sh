#!/usr/bin/env bash

: "${ACCESS_TOKEN:?ACCESS_TOKEN is required}"
: "${REPLACEMENT:?REPLACEMENT is required}"
: "${PLACEHOLDER:?PLACEHOLDER is required}"
: "${DOCUMENT_ID:?DOCUMENT_ID is required}"
DOC_JSON="$(curl -sS \
  -H "Authorization: Bearer $ACCESS_TOKEN" \
  "https://docs.googleapis.com/v1/documents/$DOCUMENT_ID?includeTabsContent=true&suggestionsViewMode=SUGGESTIONS_INLINE")"
REVISION_ID="$(printf '%s' "$DOC_JSON" | jq -r '.revisionId')"

jq -n \
  --arg find "$PLACEHOLDER" \
  --arg replace "$REPLACEMENT" \
  --arg rev "$REVISION_ID" '{
    requests: [{
      replaceAllText: {
        containsText: {text: $find, matchCase: true},
        replaceText: $replace
      }
    }],
    writeControl: {requiredRevisionId: $rev}
  }' > /tmp/docs_replace.json

curl -sS -X POST \
  -H "Authorization: Bearer $ACCESS_TOKEN" \
  -H "Content-Type: application/json" \
  "https://docs.googleapis.com/v1/documents/$DOCUMENT_ID:batchUpdate" \
  --data @/tmp/docs_replace.json \
  | jq '{documentId,replies,writeControl}'
