#!/usr/bin/env bash

MESSAGE_ID="MESSAGE_ID_HERE"

curl -fsS -X DELETE "$BASE/messages/$MESSAGE_ID" \
  -H "Authorization: Bearer $ACCESS_TOKEN"
