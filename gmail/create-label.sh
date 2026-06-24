#!/usr/bin/env bash

LABEL_NAME="Buoy/Follow Up"

jq -n --arg name "$LABEL_NAME" '{
  name: $name,
  labelListVisibility: "labelShow",
  messageListVisibility: "show"
}' |
curl -fsS -X POST "$BASE/labels" \
  -H "Authorization: Bearer $ACCESS_TOKEN" \
  -H "Content-Type: application/json" \
  --data-binary @- |
jq
