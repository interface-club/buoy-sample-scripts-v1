#!/usr/bin/env bash

DRAFT_ID="DRAFT_ID_HERE"

curl -fsS "$BASE/drafts/$DRAFT_ID?format=metadata" \
  -H "Authorization: Bearer $ACCESS_TOKEN" |
jq

# After explicit user confirmation:
jq -n --arg id "$DRAFT_ID" '{id: $id}' |
curl -fsS -X POST "$BASE/drafts/send" \
  -H "Authorization: Bearer $ACCESS_TOKEN" \
  -H "Content-Type: application/json" \
  --data-binary @- |
jq
