#!/usr/bin/env bash

: "${ACCESS_TOKEN:?ACCESS_TOKEN is required}"
: "${PRESENTATION_ID:?PRESENTATION_ID is required}"
: "${SPEAKER_NOTES_OBJECT_ID:?SPEAKER_NOTES_OBJECT_ID is required}"
: "${NEW_NOTES:?NEW_NOTES is required}"

REVISION_ID="$(curl -sS -H "Authorization: Bearer $ACCESS_TOKEN" \
  "https://slides.googleapis.com/v1/presentations/$PRESENTATION_ID?fields=revisionId" \
  | jq -r '.revisionId')"

BODY="$(jq -n \
  --arg rev "$REVISION_ID" \
  --arg obj "$SPEAKER_NOTES_OBJECT_ID" \
  --arg notes "$NEW_NOTES" \
  '{
    requests: [
      { deleteText: { objectId: $obj, textRange: { type: "ALL" } } },
      { insertText: { objectId: $obj, insertionIndex: 0, text: $notes } }
    ],
    writeControl: { requiredRevisionId: $rev }
  }')"

curl -sS -X POST \
  -H "Authorization: Bearer $ACCESS_TOKEN" \
  -H "Content-Type: application/json" \
  --data "$BODY" \
  "https://slides.googleapis.com/v1/presentations/$PRESENTATION_ID:batchUpdate" \
  | jq .
