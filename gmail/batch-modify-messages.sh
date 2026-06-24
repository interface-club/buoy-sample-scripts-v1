#!/usr/bin/env bash

IDS_JSON='["MESSAGE_ID_1","MESSAGE_ID_2"]'

jq -n --argjson ids "$IDS_JSON" '{
  ids: $ids,
  removeLabelIds: ["INBOX", "UNREAD"],
  addLabelIds: []
}' |
curl -fsS -X POST "$BASE/messages/batchModify" \
  -H "Authorization: Bearer $ACCESS_TOKEN" \
  -H "Content-Type: application/json" \
  --data-binary @-
