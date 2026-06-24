#!/usr/bin/env bash

: "${ACCESS_TOKEN:?ACCESS_TOKEN is required}"
: "${PRESENTATION_ID:?PRESENTATION_ID is required}"
: "${OBJECT_ID:?OBJECT_ID is required}"
: "${REVISION_ID:?REVISION_ID is required}"

BODY="$(jq -n --arg rev "$REVISION_ID" --arg id "$OBJECT_ID" '{
  requests: [ { deleteObject: { objectId: $id } } ],
  writeControl: { requiredRevisionId: $rev }
}')"

curl -sS -X POST \
  -H "Authorization: Bearer $ACCESS_TOKEN" \
  -H "Content-Type: application/json" \
  --data "$BODY" \
  "https://slides.googleapis.com/v1/presentations/$PRESENTATION_ID:batchUpdate" \
  | jq .
