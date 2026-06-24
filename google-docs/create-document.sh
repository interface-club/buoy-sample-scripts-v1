#!/usr/bin/env bash

: "${ACCESS_TOKEN:?ACCESS_TOKEN is required}"
: "${TITLE:?TITLE is required}"
curl -sS -X POST \
  -H "Authorization: Bearer $ACCESS_TOKEN" \
  -H "Content-Type: application/json" \
  "https://docs.googleapis.com/v1/documents" \
  -d "$(jq -n --arg title "$TITLE" '{title:$title}')" \
  | jq '{documentId,title,revisionId,url:("https://docs.google.com/document/d/" + .documentId + "/edit")}'
