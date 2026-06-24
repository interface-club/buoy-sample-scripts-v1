#!/usr/bin/env bash

MESSAGE_ID="MESSAGE_ID_HERE"

curl -fsS -X POST "$BASE/messages/$MESSAGE_ID/untrash" \
  -H "Authorization: Bearer $ACCESS_TOKEN" |
jq
