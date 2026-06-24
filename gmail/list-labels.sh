#!/usr/bin/env bash

curl -fsS \
  -H "Authorization: Bearer $ACCESS_TOKEN" \
  "$BASE/labels" |
jq -r '.labels[] | [.id, .name, .type, (.messagesUnread // 0), (.threadsUnread // 0)] | @tsv'
