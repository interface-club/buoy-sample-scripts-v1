#!/usr/bin/env bash

ORIGINAL_MESSAGE_ID="MESSAGE_ID_HERE"
TO="recipient@example.com"
BODY="Reply text here"

ORIGINAL="$(curl -fsS -G "$BASE/messages/$ORIGINAL_MESSAGE_ID" \
  -H "Authorization: Bearer $ACCESS_TOKEN" \
  --data-urlencode "format=metadata" \
  --data-urlencode "metadataHeaders=Subject" \
  --data-urlencode "metadataHeaders=Message-ID")"

THREAD_ID="$(echo "$ORIGINAL" | jq -r '.threadId')"
SUBJECT="$(echo "$ORIGINAL" | jq -r '.payload.headers[] | select(.name=="Subject") | .value')"
MESSAGE_RFC_ID="$(echo "$ORIGINAL" | jq -r '.payload.headers[] | select(.name=="Message-ID") | .value')"

PAYLOAD="$(
TO="$TO" SUBJECT="$SUBJECT" BODY="$BODY" THREAD_ID="$THREAD_ID" MESSAGE_RFC_ID="$MESSAGE_RFC_ID" python3 - <<'PY'
import base64, json, os
from email.message import EmailMessage

msg = EmailMessage()
msg["To"] = os.environ["TO"]
msg["Subject"] = os.environ["SUBJECT"]
msg["In-Reply-To"] = os.environ["MESSAGE_RFC_ID"]
msg["References"] = os.environ["MESSAGE_RFC_ID"]
msg.set_content(os.environ["BODY"])

raw = base64.urlsafe_b64encode(msg.as_bytes()).decode().rstrip("=")
print(json.dumps({"raw": raw, "threadId": os.environ["THREAD_ID"]}))
PY
)"

# Ask for explicit confirmation before sending.
curl -fsS -X POST "$BASE/messages/send" \
  -H "Authorization: Bearer $ACCESS_TOKEN" \
  -H "Content-Type: application/json" \
  --data "$PAYLOAD" |
jq
