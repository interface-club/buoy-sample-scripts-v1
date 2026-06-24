#!/usr/bin/env bash

MESSAGE_ID="MESSAGE_ID_HERE"
ADD_LABEL_ID="Label_123"

jq -n --arg add "$ADD_LABEL_ID" '{
  addLabelIds: [$add],
  removeLabelIds: []
}' |
curl -fsS -X POST "$BASE/messages/$MESSAGE_ID/modify" \
  -H "Authorization: Bearer $ACCESS_TOKEN" \
  -H "Content-Type: application/json" \
  --data-binary @- |
jq
