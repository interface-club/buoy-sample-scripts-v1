#!/usr/bin/env bash

MESSAGE_ID="MESSAGE_ID_HERE"

curl -fsS -G "$BASE/messages/$MESSAGE_ID" \
  -H "Authorization: Bearer $ACCESS_TOKEN" \
  --data-urlencode "format=full" |
jq -r '.. | objects | select((.filename? // "") != "") |
  [.filename, .mimeType, (.body.attachmentId // ""), (.body.size // 0)] | @tsv'
