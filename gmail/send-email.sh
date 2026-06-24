#!/usr/bin/env bash

TO="recipient@example.com"
SUBJECT="Subject here"
BODY="Body text here"

PAYLOAD="$(
TO="$TO" SUBJECT="$SUBJECT" BODY="$BODY" python3 - <<'PY'
import base64, json, os
from email.message import EmailMessage

msg = EmailMessage()
msg["To"] = os.environ["TO"]
msg["Subject"] = os.environ["SUBJECT"]
msg.set_content(os.environ["BODY"])

raw = base64.urlsafe_b64encode(msg.as_bytes()).decode().rstrip("=")
print(json.dumps({"raw": raw}))
PY
)"

curl -fsS -X POST "$BASE/messages/send" \
  -H "Authorization: Bearer $ACCESS_TOKEN" \
  -H "Content-Type: application/json" \
  --data "$PAYLOAD" |
jq
