#!/usr/bin/env bash

THREAD_ID="THREAD_ID_HERE"

curl -fsS -G "$BASE/threads/$THREAD_ID" \
  -H "Authorization: Bearer $ACCESS_TOKEN" \
  --data-urlencode "format=metadata" \
  --data-urlencode "metadataHeaders=From" \
  --data-urlencode "metadataHeaders=Subject" \
  --data-urlencode "metadataHeaders=Date" |
jq -r --arg email "$ACCOUNT_EMAIL" '.messages[] | {
  id,
  labelIds,
  permalink: "https://mail.google.com/mail/?authuser=\($email)#all/\(.id)",
  headers: (.payload.headers | map({(.name): .value}) | add)
}'
