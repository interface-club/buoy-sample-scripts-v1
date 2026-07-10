from __future__ import annotations

from pathlib import Path
from typing import Any

from .google_api import *

BASE = "https://api.notion.com/v1"
VERSION = "2026-03-11"


def notion_base() -> str:
    return env("NOTION_BASE_URL", BASE).rstrip("/")


def notion_json(
    method: str,
    path: str,
    *,
    query: dict[str, Any] | None = None,
    body: Any = None,
    accept: tuple[int, ...] = (200, 201, 202, 204),
) -> Any:
    return request_json(
        method,
        f"{notion_base()}{path}",
        token=access_token(),
        params=query,
        json_body=body,
        headers={
            "Notion-Version": env("NOTION_VERSION", VERSION),
            "Accept": "application/json",
        },
        accept=accept,
    )


def pagination_query() -> dict[str, Any]:
    query: dict[str, Any] = {"page_size": env_int("PAGE_SIZE", 100)}
    if env("START_CURSOR", ""):
        query["start_cursor"] = env("START_CURSOR")
    return query


def markdown_input(*, required: bool = False) -> str | None:
    path = env("MARKDOWN_PATH", "")
    if path:
        source = Path(path).expanduser()
        if not source.is_file():
            fail(f"MARKDOWN_PATH is not a file: {source}")
        return source.read_text(encoding="utf-8")
    value = env("MARKDOWN", "")
    if value:
        return value
    if required:
        fail("MARKDOWN or MARKDOWN_PATH is required")
    return None


def get_self() -> None:
    print_json(notion_json("GET", "/users/me"))


def search() -> None:
    body: dict[str, Any] = {"page_size": env_int("PAGE_SIZE", 100)}
    if env("QUERY", ""):
        body["query"] = env("QUERY")
    if env("START_CURSOR", ""):
        body["start_cursor"] = env("START_CURSOR")
    object_type = env("OBJECT_TYPE", "")
    if object_type:
        if object_type not in {"page", "data_source"}:
            fail("OBJECT_TYPE must be page or data_source")
        body["filter"] = {"property": "object", "value": object_type}
    if env("SORT_DIRECTION", ""):
        body["sort"] = {
            "timestamp": "last_edited_time",
            "direction": env("SORT_DIRECTION"),
        }
    print_json(notion_json("POST", "/search", body=body))


def get_page() -> None:
    query: dict[str, Any] = {}
    filter_properties = env_json("FILTER_PROPERTIES_JSON", None)
    if filter_properties is not None:
        if not isinstance(filter_properties, list):
            fail("FILTER_PROPERTIES_JSON must be a JSON array of property IDs")
        query["filter_properties"] = filter_properties
    print_json(notion_json("GET", f"/pages/{url_quote(env('PAGE_ID', required=True))}", query=query))


def get_page_markdown() -> None:
    query: dict[str, Any] = {}
    if env("INCLUDE_TRANSCRIPT", ""):
        query["include_transcript"] = env_bool("INCLUDE_TRANSCRIPT", False)
    print_json(notion_json("GET", f"/pages/{url_quote(env('PAGE_ID', required=True))}/markdown", query=query))


def list_block_children() -> None:
    print_json(notion_json(
        "GET",
        f"/blocks/{url_quote(env('BLOCK_ID', required=True))}/children",
        query=pagination_query(),
    ))


def get_data_source() -> None:
    print_json(notion_json("GET", f"/data_sources/{url_quote(env('DATA_SOURCE_ID', required=True))}"))


def query_data_source() -> None:
    body = env_json("BODY_JSON", None)
    if body is None:
        body = {"page_size": env_int("PAGE_SIZE", 100)}
        if env("START_CURSOR", ""):
            body["start_cursor"] = env("START_CURSOR")
        filter_body = env_json("FILTER_JSON", None)
        if filter_body is not None:
            body["filter"] = filter_body
        sorts = env_json("SORTS_JSON", None)
        if sorts is not None:
            body["sorts"] = sorts
    print_json(notion_json(
        "POST",
        f"/data_sources/{url_quote(env('DATA_SOURCE_ID', required=True))}/query",
        body=body,
    ))


def create_page() -> None:
    body = env_json("BODY_JSON", None)
    if body is None:
        page_parent = env("PARENT_PAGE_ID", "")
        data_source_parent = env("DATA_SOURCE_ID", "")
        if bool(page_parent) == bool(data_source_parent):
            fail("Set exactly one of PARENT_PAGE_ID or DATA_SOURCE_ID")
        if page_parent:
            title = env("TITLE", required=True)
            body = {
                "parent": {"type": "page_id", "page_id": page_parent},
                "properties": {
                    "title": {"title": [{"text": {"content": title}}]},
                },
            }
        else:
            body = {
                "parent": {"type": "data_source_id", "data_source_id": data_source_parent},
                "properties": env_json("PROPERTIES_JSON", required=True),
            }
        content = markdown_input()
        if content is not None:
            body["markdown"] = content
        template = env_json("TEMPLATE_JSON", None)
        if template is not None:
            body["template"] = template
        if env("ALLOW_ASYNC", ""):
            body["allow_async"] = env_bool("ALLOW_ASYNC", False)
    print_json(notion_json("POST", "/pages", body=body))


def update_page() -> None:
    body = env_json("BODY_JSON", None)
    if body is None:
        body = {}
        properties = env_json("PROPERTIES_JSON", None)
        if properties is not None:
            body["properties"] = properties
        for env_name, field_name in [
            ("ICON_JSON", "icon"),
            ("COVER_JSON", "cover"),
            ("TEMPLATE_JSON", "template"),
        ]:
            value = env_json(env_name, None)
            if value is not None:
                body[field_name] = value
        for env_name, field_name in [
            ("IN_TRASH", "in_trash"),
            ("IS_LOCKED", "is_locked"),
        ]:
            if env(env_name, ""):
                body[field_name] = env_bool(env_name, False)
        if not body:
            fail("BODY_JSON or at least one update input is required")
    print_json(notion_json("PATCH", f"/pages/{url_quote(env('PAGE_ID', required=True))}", body=body))


def update_page_markdown() -> None:
    body = env_json("BODY_JSON", None)
    if body is None:
        updates = env_json("CONTENT_UPDATES_JSON", None)
        if updates is not None:
            if not isinstance(updates, list) or not updates:
                fail("CONTENT_UPDATES_JSON must be a non-empty JSON array")
            body = {
                "type": "update_content",
                "update_content": {"content_updates": updates},
            }
        else:
            content = markdown_input(required=True)
            body = {
                "type": "replace_content",
                "replace_content": {"new_str": content},
            }
        if env("ALLOW_DELETING_CONTENT", ""):
            body[body["type"]]["allow_deleting_content"] = env_bool("ALLOW_DELETING_CONTENT", False)
        if env("ALLOW_ASYNC", ""):
            body["allow_async"] = env_bool("ALLOW_ASYNC", False)
    print_json(notion_json(
        "PATCH",
        f"/pages/{url_quote(env('PAGE_ID', required=True))}/markdown",
        body=body,
    ))


def append_block_children() -> None:
    body = env_json("BODY_JSON", None)
    if body is None:
        children = env_json("CHILDREN_JSON", None)
        content = markdown_input()
        if (children is None) == (content is None):
            fail("Set exactly one of CHILDREN_JSON or MARKDOWN/MARKDOWN_PATH")
        body = {"children": children} if children is not None else {"markdown": content}
        position = env_json("POSITION_JSON", None)
        if position is not None:
            body["position"] = position
    print_json(notion_json(
        "PATCH",
        f"/blocks/{url_quote(env('BLOCK_ID', required=True))}/children",
        body=body,
    ))


def create_database() -> None:
    body = env_json("BODY_JSON", None)
    if body is None:
        title = env("TITLE", required=True)
        body = {
            "parent": {"type": "page_id", "page_id": env("PARENT_PAGE_ID", required=True)},
            "title": [{"text": {"content": title}}],
            "initial_data_source": {
                "properties": env_json("PROPERTIES_JSON", {
                    env("TITLE_PROPERTY", "Name"): {"title": {}},
                }),
            },
            "is_inline": env_bool("IS_INLINE", False),
        }
    print_json(notion_json("POST", "/databases", body=body))


def list_comments() -> None:
    query = pagination_query()
    query["block_id"] = env("BLOCK_ID", required=True)
    print_json(notion_json("GET", "/comments", query=query))


def create_comment() -> None:
    body = env_json("BODY_JSON", None)
    if body is None:
        targets = [
            ("PAGE_ID", "page_id"),
            ("BLOCK_ID", "block_id"),
            ("DISCUSSION_ID", "discussion_id"),
        ]
        selected = [(env_name, field_name, env(env_name, "")) for env_name, field_name in targets if env(env_name, "")]
        if len(selected) != 1:
            fail("Set exactly one of PAGE_ID, BLOCK_ID, or DISCUSSION_ID")
        _, field_name, target_id = selected[0]
        body = {"discussion_id": target_id} if field_name == "discussion_id" else {"parent": {field_name: target_id}}
        markdown = env("MARKDOWN", "")
        rich_text = env_json("RICH_TEXT_JSON", None)
        if bool(markdown) == (rich_text is not None):
            fail("Set exactly one of MARKDOWN or RICH_TEXT_JSON")
        if markdown:
            body["markdown"] = markdown
        else:
            body["rich_text"] = rich_text
    print_json(notion_json("POST", "/comments", body=body))
