#!/usr/bin/env bash

: "${ACCESS_TOKEN:?ACCESS_TOKEN is required}"
: "${COMMENT_TEXT:?COMMENT_TEXT is required}"
: "${DOCUMENT_ID:?DOCUMENT_ID is required}"
curl -sS -X POST \
  -H "Authorization: Bearer $ACCESS_TOKEN" \
  -H "Content-Type: application/json" \
  "https://www.googleapis.com/drive/v3/files/$DOCUMENT_ID/comments?fields=id,content,createdTime" \
  -d "$(jq -n --arg content "$COMMENT_TEXT" '{content:$content}')" \
  | jq .
