from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from .google_api import *

BASE = "https://slack.com/api"


def slack_base() -> str:
    return env("SLACK_BASE_URL", BASE).rstrip("/")


def slack_json(
    method: str,
    name: str,
    *,
    query: dict[str, Any] | None = None,
    body: Any = None,
) -> dict[str, Any]:
    payload = request_json(
        method,
        f"{slack_base()}/{name}",
        token=access_token(),
        params=query,
        json_body=body,
    )
    if not isinstance(payload, dict):
        fail(f"Slack {name} response was not a JSON object")
    if payload.get("ok") is not True:
        fail(json.dumps(payload, indent=2, ensure_ascii=False))
    return payload


def optional_query(names: list[tuple[str, str]]) -> dict[str, Any]:
    query: dict[str, Any] = {}
    for env_name, parameter_name in names:
        value = env(env_name, "")
        if value:
            query[parameter_name] = value
    return query


def auth_test() -> None:
    print_json(slack_json("POST", "auth.test", body={}))


def list_conversations() -> None:
    query: dict[str, Any] = {
        "types": env("TYPES", "public_channel,private_channel,im,mpim"),
        "exclude_archived": env_bool("EXCLUDE_ARCHIVED", True),
        "limit": env_int("LIMIT", 200),
    }
    if active_page_token():
        query["cursor"] = active_page_token()
    if env("TEAM_ID", ""):
        query["team_id"] = env("TEAM_ID")
    print_json(slack_json("GET", "conversations.list", query=query))


def find_conversation() -> None:
    target = env("NAME", required=True).removeprefix("#").casefold()
    cursor = active_page_token()
    max_pages = env_int("MAX_PAGES", 20)
    matches: list[dict[str, Any]] = []
    scanned = 0

    for _ in range(max_pages):
        query: dict[str, Any] = {
            "types": env("TYPES", "public_channel,private_channel"),
            "exclude_archived": env_bool("EXCLUDE_ARCHIVED", True),
            "limit": env_int("LIMIT", 200),
        }
        if cursor:
            query["cursor"] = cursor
        if env("TEAM_ID", ""):
            query["team_id"] = env("TEAM_ID")
        payload = slack_json("GET", "conversations.list", query=query)
        channels = payload.get("channels") or []
        scanned += len(channels)
        matches.extend(
            channel
            for channel in channels
            if str(channel.get("name_normalized") or channel.get("name") or "").casefold()
            == target
        )
        cursor = str(payload.get("response_metadata", {}).get("next_cursor") or "")
        if matches or not cursor:
            break

    print_json({"matches": matches, "scanned": scanned, "next_cursor": cursor or None})


def conversation_history() -> None:
    query: dict[str, Any] = {
        "channel": env("CHANNEL_ID", required=True),
        "limit": env_int("LIMIT", 100),
    }
    query.update(optional_query([
        ("CURSOR", "cursor"),
        ("OLDEST", "oldest"),
        ("LATEST", "latest"),
    ]))
    if env("INCLUSIVE", ""):
        query["inclusive"] = env_bool("INCLUSIVE", False)
    if env("INCLUDE_ALL_METADATA", ""):
        query["include_all_metadata"] = env_bool("INCLUDE_ALL_METADATA", False)
    print_json(slack_json("GET", "conversations.history", query=query))


def thread_replies() -> None:
    query: dict[str, Any] = {
        "channel": env("CHANNEL_ID", required=True),
        "ts": env("THREAD_TS", required=True),
        "limit": env_int("LIMIT", 100),
    }
    query.update(optional_query([
        ("CURSOR", "cursor"),
        ("OLDEST", "oldest"),
        ("LATEST", "latest"),
    ]))
    if env("INCLUSIVE", ""):
        query["inclusive"] = env_bool("INCLUSIVE", False)
    print_json(slack_json("GET", "conversations.replies", query=query))


def search_messages() -> None:
    query: dict[str, Any] = {
        "query": env("QUERY", required=True),
        "count": env_int("COUNT", 100),
        "sort": env("SORT", "timestamp"),
        "sort_dir": env("SORT_DIR", "desc"),
    }
    query.update(optional_query([("TEAM_ID", "team_id")]))
    if active_page_token():
        query["cursor"] = active_page_token()
    if env("HIGHLIGHT", ""):
        query["highlight"] = env_bool("HIGHLIGHT", False)
    print_json(slack_json("GET", "search.messages", query=query))


def list_users() -> None:
    query: dict[str, Any] = {"limit": env_int("LIMIT", 200)}
    query.update(optional_query([("TEAM_ID", "team_id")]))
    if active_page_token():
        query["cursor"] = active_page_token()
    if env("INCLUDE_LOCALE", ""):
        query["include_locale"] = env_bool("INCLUDE_LOCALE", False)
    print_json(slack_json("GET", "users.list", query=query))


def open_conversation() -> None:
    user_ids = env_json("USER_IDS_JSON", required=True)
    if not isinstance(user_ids, list) or not user_ids or not all(
        isinstance(user_id, str) and user_id for user_id in user_ids
    ):
        fail("USER_IDS_JSON must be a non-empty JSON array of Slack user IDs")
    body: dict[str, Any] = {
        "users": ",".join(user_ids),
        "return_im": env_bool("RETURN_IM", True),
    }
    if env("PREVENT_CREATION", ""):
        body["prevent_creation"] = env_bool("PREVENT_CREATION", False)
    print_json(slack_json("POST", "conversations.open", body=body))


def post_message() -> None:
    body = env_json("BODY_JSON", None)
    if body is None:
        body = {"channel": env("CHANNEL_ID", required=True)}
        text = env("TEXT", "")
        blocks = env_json("BLOCKS_JSON", None)
        if not text and blocks is None:
            fail("TEXT or BLOCKS_JSON is required")
        if text:
            body["text"] = text
        if blocks is not None:
            body["blocks"] = blocks
        if env("THREAD_TS", ""):
            body["thread_ts"] = env("THREAD_TS")
        if env("REPLY_BROADCAST", ""):
            body["reply_broadcast"] = env_bool("REPLY_BROADCAST", False)
        if env("UNFURL_LINKS", ""):
            body["unfurl_links"] = env_bool("UNFURL_LINKS", True)
        if env("UNFURL_MEDIA", ""):
            body["unfurl_media"] = env_bool("UNFURL_MEDIA", True)
        metadata = env_json("METADATA_JSON", None)
        if metadata is not None:
            body["metadata"] = metadata
    print_json(slack_json("POST", "chat.postMessage", body=body))


def get_file_info() -> None:
    query: dict[str, Any] = {
        "file": env("FILE_ID", required=True),
        "limit": env_int("LIMIT", 100),
    }
    if env("CURSOR", ""):
        query["cursor"] = env("CURSOR")
    print_json(slack_json("GET", "files.info", query=query))


def download_file() -> None:
    file_id = env("FILE_ID", "")
    file_url = env("FILE_URL", "")
    if not file_url:
        if not file_id:
            fail("FILE_ID or FILE_URL is required")
        payload = slack_json("GET", "files.info", query={"file": file_id})
        file_object = payload.get("file") or {}
        file_url = str(file_object.get("url_private_download") or file_object.get("url_private") or "")
        if not file_url:
            fail("Slack file response did not include a private download URL")
    data = request_bytes("GET", file_url, token=access_token())
    result = write_bytes(env("OUT", required=True), data)
    result["fileId"] = file_id or None
    print_json(result)


def upload_file() -> None:
    path = Path(env("FILE_PATH", required=True)).expanduser()
    if not path.is_file():
        fail(f"FILE_PATH is not a file: {path}")

    request_body: dict[str, Any] = {
        "filename": env("FILENAME", path.name),
        "length": path.stat().st_size,
    }
    if env("ALT_TEXT", ""):
        request_body["alt_txt"] = env("ALT_TEXT")
    if env("SNIPPET_TYPE", ""):
        request_body["snippet_type"] = env("SNIPPET_TYPE")

    ticket = slack_json("POST", "files.getUploadURLExternal", body=request_body)
    upload_url = ticket.get("upload_url")
    file_id = ticket.get("file_id")
    if not isinstance(upload_url, str) or not isinstance(file_id, str):
        fail("Slack upload ticket omitted upload_url or file_id")

    request(
        "POST",
        upload_url,
        data=path.read_bytes(),
        headers={"Content-Type": guess_mime(str(path))},
        accept=(200,),
    )

    file_entry: dict[str, Any] = {"id": file_id}
    if env("TITLE", ""):
        file_entry["title"] = env("TITLE")
    complete_body: dict[str, Any] = {"files": [file_entry]}
    for env_name, field_name in [
        ("CHANNEL_ID", "channel_id"),
        ("THREAD_TS", "thread_ts"),
        ("INITIAL_COMMENT", "initial_comment"),
    ]:
        value = env(env_name, "")
        if value:
            complete_body[field_name] = value
    print_json(slack_json("POST", "files.completeUploadExternal", body=complete_body))


def add_reaction() -> None:
    print_json(slack_json("POST", "reactions.add", body={
        "channel": env("CHANNEL_ID", required=True),
        "timestamp": env("MESSAGE_TS", required=True),
        "name": env("EMOJI_NAME", required=True).strip(":"),
    }))
