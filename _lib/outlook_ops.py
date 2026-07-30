from __future__ import annotations

from .microsoft_graph import *

MESSAGE_SELECT = (
    "id,conversationId,internetMessageId,webLink,from,toRecipients,subject,"
    "receivedDateTime,sentDateTime,isRead,hasAttachments,categories,bodyPreview,"
    "parentFolderId,isDraft"
)


def me_path(suffix: str) -> str:
    return f"{graph_base()}/me{suffix}"


def message_path(message_id: str, suffix: str = "") -> str:
    return me_path(f"/messages/{url_quote(message_id)}{suffix}")


def batch_modify_messages() -> None:
    ids = env_json("IDS_JSON", required=True)
    if not isinstance(ids, list) or not ids or not all(isinstance(item, str) and item for item in ids):
        fail("IDS_JSON must be a non-empty array of message IDs")
    is_read = env_bool("IS_READ", True)
    destination_id = env("DESTINATION_ID", "archive")
    categories = env_json("CATEGORIES_JSON", None)
    if categories is not None and (
        not isinstance(categories, list)
        or not all(isinstance(item, str) and item for item in categories)
    ):
        fail("CATEGORIES_JSON must be an array of category names")
    results = []
    for offset in range(0, len(ids), 10):
        requests = []
        message_ids_by_request: dict[str, str] = {}
        for index, message_id in enumerate(ids[offset : offset + 10]):
            patch_id = f"patch-{index}"
            patch: dict[str, Any] = {"isRead": is_read}
            if categories is not None:
                patch["categories"] = categories
            requests.append(
                {
                    "id": patch_id,
                    "method": "PATCH",
                    "url": f"/me/messages/{url_quote(message_id)}",
                    "headers": {"Content-Type": "application/json"},
                    "body": patch,
                }
            )
            message_ids_by_request[patch_id] = message_id
            if destination_id:
                move_id = f"move-{index}"
                requests.append(
                    {
                        "id": move_id,
                        "dependsOn": [patch_id],
                        "method": "POST",
                        "url": f"/me/messages/{url_quote(message_id)}/move",
                        "headers": {"Content-Type": "application/json"},
                        "body": {"destinationId": destination_id},
                    }
                )
                message_ids_by_request[move_id] = message_id
        payload = request_json(
            "POST",
            f"{graph_base()}/$batch",
            token=access_token(),
            json_body={"requests": requests},
        )
        for response in payload.get("responses", []):
            results.append(
                {
                    "messageId": message_ids_by_request.get(response.get("id")),
                    "operation": str(response.get("id", "")).split("-", 1)[0],
                    "status": response.get("status"),
                    "body": response.get("body"),
                }
            )
    print_json(
        {
            "messageIDs": ids,
            "isRead": is_read,
            "destinationId": destination_id or None,
            "categories": categories,
            "results": results,
        }
    )


def create_category() -> None:
    display_name = env("CATEGORY_NAME", required=True)
    color = env("COLOR", "preset0")
    print_json(
        request_json(
            "POST",
            me_path("/outlook/masterCategories"),
            token=access_token(),
            json_body={"displayName": display_name, "color": color},
        )
    )


def create_draft() -> None:
    message = _outgoing_message()
    print_json(
        request_json(
            "POST",
            me_path("/messages"),
            token=access_token(),
            json_body=message,
        )
    )


def delete_message() -> None:
    message_id = env("MESSAGE_ID", required=True)
    status, body, _ = request(
        "DELETE",
        message_path(message_id),
        token=access_token(),
    )
    print_json({"messageId": message_id, "status": status, "deleted": body == b""})


def download_attachment() -> None:
    message_id = env("MESSAGE_ID", required=True)
    attachment_id = env("ATTACHMENT_ID", required=True)
    out = env("OUT_FILE", env("OUT", required=True))
    data = request_bytes(
        "GET",
        message_path(message_id, f"/attachments/{url_quote(attachment_id)}/$value"),
        token=access_token(),
    )
    result = write_bytes(out, data)
    result.update({"messageId": message_id, "attachmentId": attachment_id})
    print_json(result)


def find_attachments() -> None:
    message_id = env("MESSAGE_ID", required=True)
    url = message_path(message_id, "/attachments")
    params: dict[str, Any] | None = {
        "$select": "id,name,contentType,size,isInline,lastModifiedDateTime",
        "$top": min(max(env_int("PAGE_SIZE", 100), 1), 999),
    }
    attachments = []
    while url:
        payload = request_json("GET", url, token=access_token(), params=params)
        params = None
        attachments.extend(
            {
                "id": item.get("id"),
                "type": item.get("@odata.type"),
                "name": item.get("name"),
                "contentType": item.get("contentType"),
                "size": item.get("size"),
                "isInline": item.get("isInline", False),
                "lastModifiedDateTime": item.get("lastModifiedDateTime"),
            }
            for item in payload.get("value", [])
        )
        next_url = next_link(payload)
        url = trusted_graph_url(next_url) if next_url else ""
    print_json(attachments)


def get_current_account() -> None:
    print_json(
        request_json(
            "GET",
            me_path(""),
            token=access_token(),
            params={
                "$select": "id,displayName,mail,userPrincipalName",
            },
        )
    )


def list_categories() -> None:
    page_url = active_page_token()
    params = None
    if not page_url:
        page_url = me_path("/outlook/masterCategories")
        params = {"$top": min(max(env_int("PAGE_SIZE", 100), 1), 999)}
    else:
        page_url = trusted_graph_url(page_url)
    payload = request_json("GET", page_url, token=access_token(), params=params)
    print_json(
        {
            "categories": [
                {
                    "id": item.get("id"),
                    "displayName": item.get("displayName"),
                    "color": item.get("color"),
                }
                for item in payload.get("value", [])
            ],
            "nextPageToken": next_link(payload),
        }
    )


def list_mail_folders() -> None:
    page_url = active_page_token()
    params = None
    if not page_url:
        page_url = me_path("/mailFolders")
        params = {
            "includeHiddenFolders": True,
            "$top": min(max(env_int("PAGE_SIZE", 100), 1), 999),
            "$select": (
                "id,displayName,parentFolderId,childFolderCount,totalItemCount,"
                "unreadItemCount,isHidden"
            ),
        }
    else:
        page_url = trusted_graph_url(page_url)
    payload = request_json("GET", page_url, token=access_token(), params=params)
    print_json(
        {
            "folders": [
                {
                    "id": item.get("id"),
                    "displayName": item.get("displayName"),
                    "parentFolderId": item.get("parentFolderId"),
                    "childFolderCount": item.get("childFolderCount", 0),
                    "totalItemCount": item.get("totalItemCount", 0),
                    "unreadItemCount": item.get("unreadItemCount", 0),
                    "isHidden": item.get("isHidden", False),
                }
                for item in payload.get("value", [])
            ],
            "nextPageToken": next_link(payload),
        }
    )


def read_conversation() -> None:
    conversation_id = env("CONVERSATION_ID", required=True)
    escaped = conversation_id.replace("'", "''")
    url = me_path("/messages")
    params: dict[str, Any] | None = {
        "$filter": f"conversationId eq '{escaped}'",
        "$select": MESSAGE_SELECT,
        "$top": min(max(env_int("PAGE_SIZE", 100), 1), 1000),
    }
    messages = []
    while url:
        payload = request_json("GET", url, token=access_token(), params=params)
        params = None
        messages.extend(message_summary(item) for item in payload.get("value", []))
        next_url = next_link(payload)
        url = trusted_graph_url(next_url) if next_url else ""
    messages.sort(key=lambda item: item.get("receivedDateTime") or "")
    print_json(messages)


def read_message_body() -> None:
    message_id = env("MESSAGE_ID", required=True)
    message = request_json(
        "GET",
        message_path(message_id),
        token=access_token(),
        params={
            "$select": (
                f"{MESSAGE_SELECT},ccRecipients,bccRecipients,body,uniqueBody,"
                "internetMessageHeaders"
            )
        },
        headers=graph_headers(body_type="text"),
    )
    result = message_summary(message)
    result.update(
        {
            "cc": address_list(message.get("ccRecipients")),
            "bcc": address_list(message.get("bccRecipients")),
            "body": (message.get("body") or {}).get("content") or "",
            "uniqueBody": (message.get("uniqueBody") or {}).get("content") or "",
            "internetMessageHeaders": message.get("internetMessageHeaders") or [],
        }
    )
    print_json(result)


def read_message_metadata() -> None:
    message_id = env("MESSAGE_ID", required=True)
    message = request_json(
        "GET",
        message_path(message_id),
        token=access_token(),
        params={"$select": f"{MESSAGE_SELECT},ccRecipients,bccRecipients,importance,flag"},
    )
    result = message_summary(message)
    result.update(
        {
            "cc": address_list(message.get("ccRecipients")),
            "bcc": address_list(message.get("bccRecipients")),
            "importance": message.get("importance"),
            "flag": message.get("flag"),
        }
    )
    print_json(result)


def reply_to_message() -> None:
    message_id = env("MESSAGE_ID", "") or env("ORIGINAL_MESSAGE_ID", required=True)
    body = env("BODY", required=True)
    preview = request_json(
        "GET",
        message_path(message_id),
        token=access_token(),
        params={"$select": MESSAGE_SELECT},
    )
    status, response_body, _ = request(
        "POST",
        message_path(message_id, "/reply"),
        token=access_token(),
        json_body={"comment": body},
        accept=(202,),
    )
    print_json(
        {
            "preview": message_summary(preview),
            "status": status,
            "sent": response_body == b"",
        }
    )


def search_messages() -> None:
    query = env("QUERY", "from:alice@example.com")
    max_results = max(1, 12 // active_provider_connection_count("microsoft"))
    page_size = min(max(env_int("PAGE_SIZE", 100), 1), 1000)
    page_url = active_page_token()
    params = None
    if not page_url:
        page_url = me_path("/messages")
        search = query if query.startswith('"') and query.endswith('"') else f'"{query}"'
        params = {
            "$search": search,
            "$top": min(page_size, max_results),
            "$select": MESSAGE_SELECT,
        }
    else:
        page_url = trusted_graph_url(page_url)
    payload = request_json("GET", page_url, token=access_token(), params=params)
    messages = [
        message_summary(item) for item in payload.get("value", [])[:max_results]
    ]
    print_json(
        {
            "query": query,
            "messages": messages,
            "nextPageToken": next_link(payload),
        }
    )


def send_email() -> None:
    message = _outgoing_message()
    status, body, _ = request(
        "POST",
        me_path("/sendMail"),
        token=access_token(),
        json_body={"message": message, "saveToSentItems": env_bool("SAVE_TO_SENT_ITEMS", True)},
        accept=(202,),
    )
    print_json(
        {
            "status": status,
            "sent": body == b"",
            "subject": message["subject"],
            "to": address_list(message["toRecipients"]),
        }
    )


def send_existing_draft() -> None:
    draft_id = env("DRAFT_ID", required=True)
    preview = request_json(
        "GET",
        message_path(draft_id),
        token=access_token(),
        params={"$select": MESSAGE_SELECT},
    )
    if preview.get("isDraft") is not True:
        fail("The selected Outlook message is not a draft")
    status, body, _ = request(
        "POST",
        message_path(draft_id, "/send"),
        token=access_token(),
        accept=(202,),
    )
    print_json(
        {
            "preview": message_summary(preview),
            "status": status,
            "sent": body == b"",
        }
    )


def trash_message() -> None:
    _move_message("deleteditems")


def untrash_message() -> None:
    _move_message(env("DESTINATION_ID", "inbox"))


def update_message() -> None:
    message_id = env("MESSAGE_ID", required=True)
    patch = env_json("PATCH_JSON", {}) or {}
    if not isinstance(patch, dict):
        fail("PATCH_JSON must be a JSON object")
    if "IS_READ" in os.environ:
        patch["isRead"] = env_bool("IS_READ", False)
    categories = env_json("CATEGORIES_JSON", None)
    if categories is not None:
        patch["categories"] = categories
    flag_status = env("FLAG_STATUS", "")
    if flag_status:
        patch["flag"] = {"flagStatus": flag_status}
    if not patch:
        fail("Provide PATCH_JSON, IS_READ, CATEGORIES_JSON, or FLAG_STATUS")
    current = request_json(
        "GET",
        message_path(message_id),
        token=access_token(),
        params={"$select": MESSAGE_SELECT},
    )
    updated = request_json(
        "PATCH",
        message_path(message_id),
        token=access_token(),
        headers=graph_headers(etag=current.get("@odata.etag")),
        json_body=patch,
    )
    print_json({"before": message_summary(current), "after": message_summary(updated)})


def _move_message(destination_id: str) -> None:
    message_id = env("MESSAGE_ID", required=True)
    preview = request_json(
        "GET",
        message_path(message_id),
        token=access_token(),
        params={"$select": MESSAGE_SELECT},
    )
    moved = request_json(
        "POST",
        message_path(message_id, "/move"),
        token=access_token(),
        json_body={"destinationId": destination_id},
    )
    print_json(
        {
            "preview": message_summary(preview),
            "destinationId": destination_id,
            "moved": message_summary(moved),
        }
    )


def _outgoing_message() -> dict[str, Any]:
    to = env("TO", required=True)
    message: dict[str, Any] = {
        "subject": env("SUBJECT", required=True),
        "body": {
            "contentType": env("BODY_CONTENT_TYPE", "Text"),
            "content": env("BODY", required=True),
        },
        "toRecipients": email_recipients(to),
    }
    cc = env_json("CC_JSON", None)
    if cc is not None:
        message["ccRecipients"] = json_recipients(cc)
    bcc = env_json("BCC_JSON", None)
    if bcc is not None:
        message["bccRecipients"] = json_recipients(bcc)
    importance = env("IMPORTANCE", "")
    if importance:
        message["importance"] = importance
    return message
