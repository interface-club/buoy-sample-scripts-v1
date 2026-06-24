#!/usr/bin/env bash

: "${ACCESS_TOKEN:?ACCESS_TOKEN is required}"
QUERY="${QUERY:-}"
Q_PARAM=""
[ -n "$QUERY" ] && Q_PARAM="&q=$(printf '%s' "$QUERY" | jq -sRr @uri)"

curl -sS \
  -H "Authorization: Bearer $ACCESS_TOKEN" \
  "https://www.googleapis.com/drive/v3/drives?pageSize=100$Q_PARAM&fields=nextPageToken,drives(id,name,createdTime,hidden)" \
| jq .
