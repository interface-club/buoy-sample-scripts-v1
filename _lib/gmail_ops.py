from __future__ import annotations

from .google_api import *

BASE = "https://gmail.googleapis.com/gmail/v1/users/me"


def base() -> str:
    return env("BASE", BASE)


def batch_modify_messages() -> None:
    ids = env_json("IDS_JSON", required=True)
    body = {
        "ids": ids,
        "removeLabelIds": env_json("REMOVE_LABEL_IDS_JSON", ["INBOX", "UNREAD"]),
        "addLabelIds": env_json("ADD_LABEL_IDS_JSON", []),
    }
    print_json(request_json("POST", f"{base()}/messages/batchModify", token=access_token(), json_body=body))


def create_draft() -> None:
    to = env("TO", required=True)
    subject = env("SUBJECT", required=True)
    body = env("BODY", required=True)
    payload = {"message": {"raw": email_raw(to=to, subject=subject, body=body)}}
    print_json(request_json("POST", f"{base()}/drafts", token=access_token(), json_body=payload))


def create_label() -> None:
    name = env("LABEL_NAME", required=True)
    body = {
        "name": name,
        "labelListVisibility": env("LABEL_LIST_VISIBILITY", "labelShow"),
        "messageListVisibility": env("MESSAGE_LIST_VISIBILITY", "show"),
    }
    print_json(request_json("POST", f"{base()}/labels", token=access_token(), json_body=body))


def delete_message() -> None:
    message_id = env("MESSAGE_ID", required=True)
    status, body, _ = request("DELETE", f"{base()}/messages/{url_quote(message_id)}", token=access_token())
    print_json({"messageId": message_id, "status": status, "deleted": body == b""})


def download_attachment() -> None:
    message_id = env("MESSAGE_ID", required=True)
    attachment_id = env("ATTACHMENT_ID", required=True)
    out = env("OUT_FILE", env("OUT", required=True))
    payload = request_json("GET", f"{base()}/messages/{url_quote(message_id)}/attachments/{url_quote(attachment_id)}", token=access_token())
    result = write_bytes(out, b64url_decode(payload.get("data")))
    result.update({"messageId": message_id, "attachmentId": attachment_id})
    print_json(result)


def find_attachments() -> None:
    message_id = env("MESSAGE_ID", required=True)
    msg = request_json("GET", f"{base()}/messages/{url_quote(message_id)}", token=access_token(), params={"format": "full"})
    found = []
    def walk(part: dict[str, Any]) -> None:
        filename = part.get("filename") or ""
        body = part.get("body", {}) or {}
        if filename:
            found.append({"filename": filename, "mimeType": part.get("mimeType"), "attachmentId": body.get("attachmentId", ""), "size": body.get("size", 0)})
        for child in part.get("parts", []) or []:
            walk(child)
    walk(msg.get("payload", {}))
    print_json(found)


def get_current_account() -> None:
    print_json(request_json("GET", f"{base()}/profile", token=access_token()))


def list_labels() -> None:
    payload = request_json("GET", f"{base()}/labels", token=access_token())
    print_json([
        {"id": label.get("id"), "name": label.get("name"), "type": label.get("type"), "messagesUnread": label.get("messagesUnread", 0), "threadsUnread": label.get("threadsUnread", 0)}
        for label in payload.get("labels", [])
    ])


def modify_message_labels() -> None:
    message_id = env("MESSAGE_ID", required=True)
    add = env_json("ADD_LABEL_IDS_JSON", None)
    if add is None:
        one = env("ADD_LABEL_ID", "")
        add = [one] if one else []
    remove = env_json("REMOVE_LABEL_IDS_JSON", [])
    body = {"addLabelIds": add, "removeLabelIds": remove}
    print_json(request_json("POST", f"{base()}/messages/{url_quote(message_id)}/modify", token=access_token(), json_body=body))


def read_message_body() -> None:
    message_id = env("MESSAGE_ID", required=True)
    msg = request_json("GET", f"{base()}/messages/{url_quote(message_id)}", token=access_token(), params={"format": "full"})
    headers = header_map(msg)
    print_json({
        "id": msg.get("id"),
        "threadId": msg.get("threadId"),
        "from": headers.get("from", ""),
        "to": headers.get("to", ""),
        "subject": headers.get("subject", ""),
        "date": headers.get("date", ""),
        "permalink": gmail_permalink(msg.get("id", "")),
        "body": first_plain_text(msg.get("payload", {})),
    })


def read_message_metadata() -> None:
    message_id = env("MESSAGE_ID", required=True)
    headers = ["From", "To", "Cc", "Subject", "Date", "Message-ID"]
    params = [("format", "metadata"), *[("metadataHeaders", h) for h in headers]]
    msg = request_json("GET", f"{base()}/messages/{url_quote(message_id)}", token=access_token(), params=params)
    msg["permalink"] = gmail_permalink(msg.get("id", ""))
    print_json(msg)


def read_thread() -> None:
    thread_id = env("THREAD_ID", required=True)
    params = [("format", "metadata"), ("metadataHeaders", "From"), ("metadataHeaders", "Subject"), ("metadataHeaders", "Date")]
    thread = request_json("GET", f"{base()}/threads/{url_quote(thread_id)}", token=access_token(), params=params)
    print_json([
        {"id": msg.get("id"), "labelIds": msg.get("labelIds", []), "permalink": gmail_permalink(msg.get("id", "")), "headers": header_map(msg)}
        for msg in thread.get("messages", [])
    ])


def reply_in_thread() -> None:
    original_id = env("ORIGINAL_MESSAGE_ID", required=True)
    to = env("TO", required=True)
    body_text = env("BODY", required=True)
    original = request_json("GET", f"{base()}/messages/{url_quote(original_id)}", token=access_token(), params=[("format", "metadata"), ("metadataHeaders", "Subject"), ("metadataHeaders", "Message-ID")])
    headers = header_map(original)
    raw = email_raw(to=to, subject=headers.get("subject", ""), body=body_text, headers={"In-Reply-To": headers.get("message-id", ""), "References": headers.get("message-id", "")})
    payload = {"raw": raw, "threadId": original.get("threadId")}
    print_json(request_json("POST", f"{base()}/messages/send", token=access_token(), json_body=payload))


def search_messages() -> None:
    query = env("QUERY", "from:alice@example.com newer_than:30d -in:trash")
    max_total = env_int("MAX_TOTAL", 200)
    page_size = min(env_int("PAGE_SIZE", 100), 500)
    page_token = env("PAGE_TOKEN", "")
    results = []
    while True:
        params = {"q": query, "maxResults": page_size}
        if page_token:
            params["pageToken"] = page_token
        payload = request_json("GET", f"{base()}/messages", token=access_token(), params=params)
        for msg in payload.get("messages", []):
            results.append({"id": msg.get("id"), "threadId": msg.get("threadId"), "permalink": gmail_permalink(msg.get("id", ""))})
            if len(results) >= max_total:
                break
        page_token = payload.get("nextPageToken") or ""
        if not page_token or len(results) >= max_total:
            break
    print_json({"query": query, "messages": results, "nextPageToken": page_token or None})


def send_email() -> None:
    payload = {"raw": email_raw(to=env("TO", required=True), subject=env("SUBJECT", required=True), body=env("BODY", required=True))}
    print_json(request_json("POST", f"{base()}/messages/send", token=access_token(), json_body=payload))


def send_existing_draft() -> None:
    draft_id = env("DRAFT_ID", required=True)
    preview = request_json("GET", f"{base()}/drafts/{url_quote(draft_id)}", token=access_token(), params={"format": "metadata"})
    sent = request_json("POST", f"{base()}/drafts/send", token=access_token(), json_body={"id": draft_id})
    print_json({"preview": preview, "sent": sent})


def trash_message() -> None:
    message_id = env("MESSAGE_ID", required=True)
    print_json(request_json("POST", f"{base()}/messages/{url_quote(message_id)}/trash", token=access_token()))


def untrash_message() -> None:
    message_id = env("MESSAGE_ID", required=True)
    print_json(request_json("POST", f"{base()}/messages/{url_quote(message_id)}/untrash", token=access_token()))
