#!/usr/bin/env bash

MESSAGE_ID="MESSAGE_ID_HERE"
ATTACHMENT_ID="ATTACHMENT_ID_HERE"
OUT_FILE="/tmp/attachment.bin"

curl -fsS \
  -H "Authorization: Bearer $ACCESS_TOKEN" \
  "$BASE/messages/$MESSAGE_ID/attachments/$ATTACHMENT_ID" |
jq -r '.data' |
python3 -c 'import sys,base64; s=sys.stdin.read().strip(); sys.stdout.buffer.write(base64.urlsafe_b64decode(s + "="*((4-len(s)%4)%4)))' \
  > "$OUT_FILE"
