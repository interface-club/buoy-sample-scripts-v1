from __future__ import annotations

from typing import Any
from urllib.parse import urlparse

from .google_api import *

CLOUD_BASE_URLS = ("https://us.posthog.com", "https://eu.posthog.com")


def _api_base_url() -> str:
    value = connection_field("apiBaseURL")
    if value not in CLOUD_BASE_URLS:
        fail("The active PostHog connection is missing valid Cloud region metadata. Reconnect it.")
    return value


def _trusted_page_url(value: str, base_url: str) -> str:
    parsed = urlparse(value)
    base = urlparse(base_url)
    if parsed.scheme != base.scheme or parsed.netloc != base.netloc or not parsed.path.startswith("/api/"):
        fail("PostHog pagination URL must stay on the selected API origin under /api/")
    return value


def posthog_json(
    method: str,
    path: str,
    *,
    query: dict[str, Any] | None = None,
    body: Any = None,
    accept: tuple[int, ...] = (200, 201, 202, 204),
) -> Any:
    base_url = _api_base_url()
    return request_json(
        method,
        f"{base_url}{path}",
        token=access_token(),
        params=query,
        json_body=body,
        headers={"Accept": "application/json"},
        accept=accept,
    )


def paginated_get(path: str, query: dict[str, Any]) -> Any:
    base_url = _api_base_url()
    page_token = active_page_token()
    if page_token:
        result = request_json(
            "GET",
            _trusted_page_url(page_token, base_url),
            token=access_token(),
            headers={"Accept": "application/json"},
        )
    else:
        result = posthog_json("GET", path, query=query)
    if isinstance(result, dict) and isinstance(result.get("next"), str):
        return {**result, "nextPageToken": result["next"]}
    return result


def pagination_query() -> dict[str, Any]:
    query: dict[str, Any] = {"limit": env_int("LIMIT", 100)}
    if env("OFFSET", ""):
        query["offset"] = env_int("OFFSET", 0)
    if env("SEARCH", ""):
        query["search"] = env("SEARCH")
    return query


def get_current_user() -> None:
    base_url = _api_base_url()
    identity = request_json(
        "GET",
        f"{base_url}/api/users/@me/",
        token=access_token(),
        headers={"Accept": "application/json"},
    )
    print_json({"baseURL": base_url, "user": identity})


def list_organizations() -> None:
    print_json(paginated_get("/api/organizations/", pagination_query()))


def list_projects() -> None:
    organization_id = url_quote(env("ORGANIZATION_ID", required=True))
    print_json(
        paginated_get(
            f"/api/organizations/{organization_id}/projects/",
            pagination_query(),
        )
    )


def list_insights() -> None:
    query = pagination_query()
    query["basic"] = env_bool("BASIC", True)
    if env("SAVED", ""):
        query["saved"] = env_bool("SAVED", True)
    if env("INSIGHT_TYPE", ""):
        query["insight"] = env("INSIGHT_TYPE")
    project_id = url_quote(env("PROJECT_ID", required=True))
    print_json(paginated_get(f"/api/projects/{project_id}/insights/", query))


def get_insight() -> None:
    project_id = url_quote(env("PROJECT_ID", required=True))
    insight_id = url_quote(env("INSIGHT_ID", required=True))
    print_json(posthog_json("GET", f"/api/projects/{project_id}/insights/{insight_id}/"))


def list_dashboards() -> None:
    project_id = url_quote(env("PROJECT_ID", required=True))
    print_json(paginated_get(f"/api/projects/{project_id}/dashboards/", pagination_query()))


def list_feature_flags() -> None:
    query = pagination_query()
    for env_name, key in (
        ("KEY", "key"),
        ("ACTIVE", "active"),
        ("ARCHIVED", "archived"),
        ("FLAG_TYPE", "type"),
        ("EVALUATION_RUNTIME", "evaluation_runtime"),
    ):
        if env(env_name, ""):
            query[key] = env(env_name)
    project_id = url_quote(env("PROJECT_ID", required=True))
    print_json(paginated_get(f"/api/projects/{project_id}/feature_flags/", query))


def get_feature_flag() -> None:
    project_id = url_quote(env("PROJECT_ID", required=True))
    flag_id = url_quote(env("FLAG_ID", required=True))
    print_json(posthog_json("GET", f"/api/projects/{project_id}/feature_flags/{flag_id}/"))


def update_feature_flag() -> None:
    body = env_json("BODY_JSON", required=True)
    if not isinstance(body, dict) or not body:
        fail("BODY_JSON must be a non-empty JSON object")
    project_id = url_quote(env("PROJECT_ID", required=True))
    flag_id = url_quote(env("FLAG_ID", required=True))
    print_json(
        posthog_json(
            "PATCH",
            f"/api/projects/{project_id}/feature_flags/{flag_id}/",
            body=body,
        )
    )


def list_annotations() -> None:
    project_id = url_quote(env("PROJECT_ID", required=True))
    print_json(paginated_get(f"/api/projects/{project_id}/annotations/", pagination_query()))


def create_annotation() -> None:
    body = env_json("BODY_JSON", None)
    if body is None:
        body = {
            "content": env("CONTENT", required=True),
            "scope": env("SCOPE", "project"),
            "creation_type": env("CREATION_TYPE", "USR"),
        }
        for env_name, key in (
            ("DATE_MARKER", "date_marker"),
            ("DASHBOARD_ID", "dashboard_id"),
            ("DASHBOARD_ITEM_ID", "dashboard_item"),
            ("EMOJI", "emoji"),
        ):
            if env(env_name, ""):
                body[key] = env(env_name)
    if not isinstance(body, dict) or not body:
        fail("BODY_JSON must be a non-empty JSON object")
    project_id = url_quote(env("PROJECT_ID", required=True))
    print_json(posthog_json("POST", f"/api/projects/{project_id}/annotations/", body=body))


def run_query() -> None:
    body = env_json("BODY_JSON", None)
    if body is None:
        body = {
            "query": {
                "kind": "HogQLQuery",
                "query": env("QUERY", required=True),
            }
        }
        if env("QUERY_NAME", ""):
            body["name"] = env("QUERY_NAME")
    if not isinstance(body, dict) or not body:
        fail("BODY_JSON must be a non-empty JSON object")
    project_id = url_quote(env("PROJECT_ID", required=True))
    print_json(posthog_json("POST", f"/api/projects/{project_id}/query/", body=body))
