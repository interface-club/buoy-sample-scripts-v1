#!/usr/bin/env bash

: "${ACCESS_TOKEN:?ACCESS_TOKEN is required}"
: "${REPLACEMENTS_JSON:?REPLACEMENTS_JSON is required}"
: "${PRESENTATION_ID:?PRESENTATION_ID is required}"

REVISION_ID="$(curl -sS -H "Authorization: Bearer $ACCESS_TOKEN" \
  "https://slides.googleapis.com/v1/presentations/$PRESENTATION_ID?fields=revisionId" \
  | jq -r '.revisionId')"

BODY="$(jq -n --arg rev "$REVISION_ID" --argjson replacements "$REPLACEMENTS_JSON" '{
  requests: ($replacements | to_entries | map({
    replaceAllText: {
      containsText: {text: .key, matchCase: true},
      replaceText: .value
    }
  })),
  writeControl: {requiredRevisionId: $rev}
}')"

curl -sS -X POST \
  -H "Authorization: Bearer $ACCESS_TOKEN" \
  -H "Content-Type: application/json" \
  --data "$BODY" \
  "https://slides.googleapis.com/v1/presentations/$PRESENTATION_ID:batchUpdate" \
  | jq .
