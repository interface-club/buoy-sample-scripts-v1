#!/usr/bin/env bash

: "${ACCESS_TOKEN:?ACCESS_TOKEN is required}"
: "${DOCUMENT_ID:?DOCUMENT_ID is required}"
curl -sS \
  -H "Authorization: Bearer $ACCESS_TOKEN" \
  "https://www.googleapis.com/drive/v3/files/$DOCUMENT_ID/comments?fields=nextPageToken,comments(id,content,author(displayName,emailAddress),createdTime,modifiedTime,resolved,replies(id,content,author(displayName,emailAddress),createdTime))&includeDeleted=false" \
  | jq .
