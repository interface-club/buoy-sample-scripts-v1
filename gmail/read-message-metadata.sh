#!/usr/bin/env bash

MESSAGE_ID="MESSAGE_ID_HERE"

curl -fsS -G "$BASE/messages/$MESSAGE_ID" \
  -H "Authorization: Bearer $ACCESS_TOKEN" \
  --data-urlencode "format=metadata" \
  --data-urlencode "metadataHeaders=From" \
  --data-urlencode "metadataHeaders=To" \
  --data-urlencode "metadataHeaders=Cc" \
  --data-urlencode "metadataHeaders=Subject" \
  --data-urlencode "metadataHeaders=Date" \
  --data-urlencode "metadataHeaders=Message-ID" |
jq --arg email "$ACCOUNT_EMAIL" '. + {permalink: "https://mail.google.com/mail/?authuser=\($email)#all/\(.id)"}'
