#!/usr/bin/env bash

: "${ACCESS_TOKEN:?ACCESS_TOKEN is required}"
: "${TITLE:?TITLE is required}"
curl -sS -X POST \
  -H "Authorization: Bearer $ACCESS_TOKEN" \
  -H "Content-Type: application/json" \
  --data "$(jq -n --arg title "$TITLE" '{title:$title}')" \
  "https://slides.googleapis.com/v1/presentations" \
  | jq '{presentationId,title}'
