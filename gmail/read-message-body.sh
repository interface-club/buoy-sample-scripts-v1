#!/usr/bin/env bash

MESSAGE_ID="MESSAGE_ID_HERE"

curl -fsS -G "$BASE/messages/$MESSAGE_ID" \
  -H "Authorization: Bearer $ACCESS_TOKEN" \
  --data-urlencode "format=full" > /tmp/gmail-message.json

ACCOUNT_EMAIL="$ACCOUNT_EMAIL" python3 - <<'PY'
import base64, json, os

msg = json.load(open("/tmp/gmail-message.json"))

def b64url_decode(data):
    if not data:
        return ""
    data += "=" * ((4 - len(data) % 4) % 4)
    return base64.urlsafe_b64decode(data).decode("utf-8", "replace")

def walk(part):
    if part.get("mimeType") == "text/plain" and part.get("body", {}).get("data"):
        return b64url_decode(part["body"]["data"])
    for child in part.get("parts", []) or []:
        text = walk(child)
        if text:
            return text
    return ""

headers = {h["name"].lower(): h["value"] for h in msg.get("payload", {}).get("headers", [])}
print("From:", headers.get("from", ""))
print("Subject:", headers.get("subject", ""))
print("Permalink:", f"https://mail.google.com/mail/?authuser={os.environ['ACCOUNT_EMAIL']}#all/{msg['id']}")
print()
print(walk(msg.get("payload", {})))
PY
