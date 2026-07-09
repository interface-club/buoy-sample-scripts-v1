from __future__ import annotations

import json
from typing import Any

from .google_api import *

BASE = "https://api.linear.app/graphql"

ISSUE_FIELDS = """
id
identifier
number
title
description
url
priority
priorityLabel
estimate
createdAt
updatedAt
archivedAt
dueDate
team { id key name }
state { id name type position }
assignee { id name displayName email }
creator { id name displayName email }
labels(first: 50) { nodes { id name color } }
"""

SEARCH_RESULT_FIELDS = """
id
identifier
number
title
url
priority
priorityLabel
createdAt
updatedAt
archivedAt
team { id key name }
state { id name type position }
assignee { id name displayName email }
metadata
"""

COMMENT_FIELDS = """
id
body
createdAt
updatedAt
url
user { id name displayName email }
parent { id }
"""

HISTORY_FIELDS = """
id
createdAt
updatedAt
actor { id name displayName email }
fromState { id name type }
toState { id name type }
fromAssignee { id name displayName email }
toAssignee { id name displayName email }
fromPriority
toPriority
fromTitle
toTitle
addedLabelIds
removedLabelIds
fromDueDate
toDueDate
changes
"""


def graphql(query: str, variables: dict[str, Any] | None = None) -> Any:
    payload = request_json(
        "POST",
        env("LINEAR_GRAPHQL_URL", BASE),
        token=access_token(),
        json_body={"query": query, "variables": variables or {}},
    )
    if isinstance(payload, dict) and payload.get("errors"):
        fail(json.dumps(payload["errors"], indent=2, ensure_ascii=False))
    return payload.get("data") if isinstance(payload, dict) else payload


def _connection_args() -> dict[str, Any]:
    args: dict[str, Any] = {"first": env_int("FIRST", 50), "includeArchived": env_bool("INCLUDE_ARCHIVED", False)}
    if env("AFTER", ""):
        args["after"] = env("AFTER")
    return args


def get_viewer() -> None:
    print_json(graphql("""
query Viewer {
  viewer { id name displayName email url active admin }
}
""")["viewer"])


def list_teams() -> None:
    print_json(graphql("""
query Teams($first: Int, $after: String, $includeArchived: Boolean) {
  teams(first: $first, after: $after, includeArchived: $includeArchived) {
    nodes { id key name description url private archivedAt }
    pageInfo { hasNextPage endCursor }
  }
}
""", _connection_args())["teams"])


def list_users() -> None:
    variables = _connection_args()
    variables["includeDisabled"] = env_bool("INCLUDE_DISABLED", False)
    print_json(graphql("""
query Users($first: Int, $after: String, $includeArchived: Boolean, $includeDisabled: Boolean) {
  users(first: $first, after: $after, includeArchived: $includeArchived, includeDisabled: $includeDisabled) {
    nodes { id name displayName email url active admin isMe }
    pageInfo { hasNextPage endCursor }
  }
}
""", variables)["users"])


def list_workflow_states() -> None:
    variables = _connection_args()
    team_id = env("TEAM_ID", "")
    variables["filter"] = {"team": {"id": {"eq": team_id}}} if team_id else None
    print_json(graphql("""
query WorkflowStates($first: Int, $after: String, $includeArchived: Boolean, $filter: WorkflowStateFilter) {
  workflowStates(first: $first, after: $after, includeArchived: $includeArchived, filter: $filter) {
    nodes { id name type position color team { id key name } }
    pageInfo { hasNextPage endCursor }
  }
}
""", variables)["workflowStates"])


def list_labels() -> None:
    variables = _connection_args()
    team_id = env("TEAM_ID", "")
    variables["filter"] = {"team": {"id": {"eq": team_id}}} if team_id else None
    print_json(graphql("""
query IssueLabels($first: Int, $after: String, $includeArchived: Boolean, $filter: IssueLabelFilter) {
  issueLabels(first: $first, after: $after, includeArchived: $includeArchived, filter: $filter) {
    nodes { id name color description team { id key name } parent { id name } }
    pageInfo { hasNextPage endCursor }
  }
}
""", variables)["issueLabels"])


def search_issues() -> None:
    variables = _connection_args()
    variables.update({
        "term": env("TERM", required=True),
        "includeComments": env_bool("INCLUDE_COMMENTS", True),
        "teamId": env("TEAM_ID", "") or None,
        "filter": env_json("FILTER_JSON", None),
    })
    print_json(graphql(f"""
query SearchIssues($term: String!, $first: Int, $after: String, $includeArchived: Boolean, $includeComments: Boolean, $teamId: String, $filter: IssueFilter) {{
  searchIssues(term: $term, first: $first, after: $after, includeArchived: $includeArchived, includeComments: $includeComments, teamId: $teamId, filter: $filter) {{
    nodes {{
      {SEARCH_RESULT_FIELDS}
    }}
    pageInfo {{ hasNextPage endCursor }}
    totalCount
  }}
}}
""", variables)["searchIssues"])


def get_issue() -> None:
    variables = {"id": env("ISSUE_ID", required=True), "commentsFirst": env_int("COMMENTS_FIRST", 50), "historyFirst": env_int("HISTORY_FIRST", 50)}
    print_json(graphql(f"""
query Issue($id: String!, $commentsFirst: Int, $historyFirst: Int) {{
  issue(id: $id) {{
    {ISSUE_FIELDS}
    comments(first: $commentsFirst) {{
      nodes {{ {COMMENT_FIELDS} }}
      pageInfo {{ hasNextPage endCursor }}
    }}
    history(first: $historyFirst) {{
      nodes {{ {HISTORY_FIELDS} }}
      pageInfo {{ hasNextPage endCursor }}
    }}
  }}
}}
""", variables)["issue"])


def create_issue() -> None:
    input_body = env_json("INPUT_JSON", None)
    if input_body is None:
        input_body = {
            "teamId": env("TEAM_ID", required=True),
            "title": env("TITLE", required=True),
        }
        for env_name, key in [
            ("DESCRIPTION", "description"),
            ("ASSIGNEE_ID", "assigneeId"),
            ("STATE_ID", "stateId"),
            ("PROJECT_ID", "projectId"),
            ("CYCLE_ID", "cycleId"),
            ("DUE_DATE", "dueDate"),
            ("PARENT_ID", "parentId"),
        ]:
            value = env(env_name, "")
            if value:
                input_body[key] = value
        if env("PRIORITY", ""):
            input_body["priority"] = env_int("PRIORITY", 0)
        labels = env_json("LABEL_IDS_JSON", None)
        if labels is not None:
            input_body["labelIds"] = labels
    print_json(graphql(f"""
mutation CreateIssue($input: IssueCreateInput!) {{
  issueCreate(input: $input) {{
    success
    issue {{ {ISSUE_FIELDS} }}
  }}
}}
""", {"input": input_body})["issueCreate"])


def update_issue() -> None:
    input_body = env_json("INPUT_JSON", None)
    if input_body is None:
        input_body = {}
        for env_name, key in [
            ("TITLE", "title"),
            ("DESCRIPTION", "description"),
            ("ASSIGNEE_ID", "assigneeId"),
            ("STATE_ID", "stateId"),
            ("TEAM_ID", "teamId"),
            ("PROJECT_ID", "projectId"),
            ("CYCLE_ID", "cycleId"),
            ("DUE_DATE", "dueDate"),
            ("PARENT_ID", "parentId"),
        ]:
            value = env(env_name, "")
            if value:
                input_body[key] = value
        if env("PRIORITY", ""):
            input_body["priority"] = env_int("PRIORITY", 0)
        for env_name, key in [
            ("LABEL_IDS_JSON", "labelIds"),
            ("ADDED_LABEL_IDS_JSON", "addedLabelIds"),
            ("REMOVED_LABEL_IDS_JSON", "removedLabelIds"),
        ]:
            value = env_json(env_name, None)
            if value is not None:
                input_body[key] = value
    print_json(graphql(f"""
mutation UpdateIssue($id: String!, $input: IssueUpdateInput!) {{
  issueUpdate(id: $id, input: $input) {{
    success
    issue {{ {ISSUE_FIELDS} }}
  }}
}}
""", {"id": env("ISSUE_ID", required=True), "input": input_body})["issueUpdate"])


def add_comment() -> None:
    input_body = env_json("INPUT_JSON", None)
    if input_body is None:
        input_body = {"issueId": env("ISSUE_ID", required=True), "body": env("BODY", required=True)}
        if env("PARENT_ID", ""):
            input_body["parentId"] = env("PARENT_ID")
    print_json(graphql(f"""
mutation AddComment($input: CommentCreateInput!) {{
  commentCreate(input: $input) {{
    success
    comment {{ {COMMENT_FIELDS} }}
  }}
}}
""", {"input": input_body})["commentCreate"])
