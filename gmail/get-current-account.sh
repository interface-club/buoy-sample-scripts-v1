#!/usr/bin/env bash

curl -fsS \
  -H "Authorization: Bearer $ACCESS_TOKEN" \
  "$BASE/profile" | jq
