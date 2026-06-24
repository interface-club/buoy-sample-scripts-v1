#!/usr/bin/env bash

MESSAGE_ID="MESSAGE_ID_HERE"

curl -fsS -X POST "$BASE/messages/$MESSAGE_ID/trash" \
  -H "Authorization: Bearer $ACCESS_TOKEN" |
jq
