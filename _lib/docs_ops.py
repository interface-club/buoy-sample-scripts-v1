from __future__ import annotations

import re
from .google_api import *

DOCS = "https://docs.googleapis.com/v1"
DRIVE = "https://www.googleapis.com/drive/v3"


def add_comment() -> None:
    print_json(request_json("POST", f"{DRIVE}/files/{url_quote(env('DOCUMENT_ID', required=True))}/comments", token=access_token(), params={"fields": "id,content,createdTime"}, json_body={"content": env("COMMENT_TEXT", required=True)}))


def append_text() -> None:
    doc_id = env("DOCUMENT_ID", required=True)
    doc = request_json("GET", f"{DOCS}/documents/{url_quote(doc_id)}", token=access_token(), params={"includeTabsContent": True, "suggestionsViewMode": "SUGGESTIONS_INLINE"})
    tab_id = env("TAB_ID", "") or ((doc.get("tabs") or [{}])[0].get("tabProperties", {}).get("tabId"))
    body = {"requests": [{"insertText": {"text": env("TEXT", required=True), "endOfSegmentLocation": {"tabId": tab_id}}}], "writeControl": {"requiredRevisionId": doc.get("revisionId")}}
    result = request_json("POST", f"{DOCS}/documents/{url_quote(doc_id)}:batchUpdate", token=access_token(), json_body=body)
    print_json({"documentId": result.get("documentId"), "writeControl": result.get("writeControl")})


def copy_template() -> None:
    result = request_json("POST", f"{DRIVE}/files/{url_quote(env('TEMPLATE_ID', required=True))}/copy", token=access_token(), params={"supportsAllDrives": True, "fields": "id,name,webViewLink"}, json_body={"name": env("NEW_TITLE", required=True)})
    print_json(result)


def create_document() -> None:
    result = request_json("POST", f"{DOCS}/documents", token=access_token(), json_body={"title": env("TITLE", required=True)})
    print_json({"documentId": result.get("documentId"), "title": result.get("title"), "revisionId": result.get("revisionId"), "url": f"https://docs.google.com/document/d/{result.get('documentId')}/edit"})


def delete_document() -> None:
    doc_id = env("DOCUMENT_ID", required=True)
    status, body, _ = request("DELETE", f"{DRIVE}/files/{url_quote(doc_id)}", token=access_token(), params={"supportsAllDrives": True})
    print_json({"documentId": doc_id, "status": status, "deleted": body == b""})


def export_document() -> None:
    doc_id = env("DOCUMENT_ID", required=True)
    data = request_bytes("GET", f"{DRIVE}/files/{url_quote(doc_id)}/export", token=access_token(), params={"mimeType": env("MIME_TYPE", "application/pdf")})
    result = write_bytes(env("OUT", "document.pdf"), data)
    result["documentId"] = doc_id
    print_json(result)


def extract_document_id() -> None:
    url = env("DOC_URL", required=True)
    match = re.search(r"docs\.google\.com/document/d/([^/]+)", url)
    print_json({"documentId": match.group(1) if match else url})


def find_documents() -> None:
    query_text = drive_query_literal(env("QUERY", required=True))
    drive_q = f"mimeType = 'application/vnd.google-apps.document' and trashed = false and name contains '{query_text}'"
    params = {"q": drive_q, "pageSize": env_int("PAGE_SIZE", 10), "fields": "nextPageToken,incompleteSearch,files(id,name,webViewLink,modifiedTime,owners(emailAddress),capabilities(canEdit,canShare))", "supportsAllDrives": True, "includeItemsFromAllDrives": True}
    if active_page_token():
        params["pageToken"] = active_page_token()
    print_json(request_json("GET", f"{DRIVE}/files", token=access_token(), params=params))


def format_text_range() -> None:
    doc_id = env("DOCUMENT_ID", required=True)
    doc = request_json("GET", f"{DOCS}/documents/{url_quote(doc_id)}", token=access_token(), params={"includeTabsContent": True, "suggestionsViewMode": "SUGGESTIONS_INLINE"})
    style = env_json("TEXT_STYLE_JSON", {"bold": True})
    fields = env("FIELDS", ",".join(style.keys()))
    body = {"requests": [{"updateTextStyle": {"range": {"tabId": env("TAB_ID", required=True), "startIndex": env_int("START_INDEX", 0), "endIndex": env_int("END_INDEX", 0)}, "textStyle": style, "fields": fields}}], "writeControl": {"requiredRevisionId": doc.get("revisionId")}}
    result = request_json("POST", f"{DOCS}/documents/{url_quote(doc_id)}:batchUpdate", token=access_token(), json_body=body)
    print_json({"documentId": result.get("documentId"), "writeControl": result.get("writeControl")})


def inspect_delete_target() -> None:
    print_json(request_json("GET", f"{DRIVE}/files/{url_quote(env('DOCUMENT_ID', required=True))}", token=access_token(), params={"fields": "id,name,webViewLink,ownedByMe,owners(emailAddress),trashed,capabilities(canTrash,canDelete)", "supportsAllDrives": True}))


def inspect_sharing() -> None:
    print_json(request_json("GET", f"{DRIVE}/files/{url_quote(env('DOCUMENT_ID', required=True))}", token=access_token(), params={"fields": "id,name,webViewLink,owners(emailAddress),permissions(id,type,role,emailAddress,domain)", "supportsAllDrives": True}))


def inspect_structural_indexes() -> None:
    doc = request_json("GET", f"{DOCS}/documents/{url_quote(env('DOCUMENT_ID', required=True))}", token=access_token(), params={"includeTabsContent": True, "suggestionsViewMode": "SUGGESTIONS_INLINE"})
    target_tab = env("TAB_ID", "")
    print_json([{"tabId": tab.get("tabProperties", {}).get("tabId"), "title": tab.get("tabProperties", {}).get("title"), "blocks": docs_blocks(tab)} for tab in all_tabs(doc.get("tabs", [])) if not target_tab or tab.get("tabProperties", {}).get("tabId") == target_tab])


def list_comments() -> None:
    print_json(request_json("GET", f"{DRIVE}/files/{url_quote(env('DOCUMENT_ID', required=True))}/comments", token=access_token(), params={"fields": "nextPageToken,comments(id,content,author(displayName,emailAddress),createdTime,modifiedTime,resolved,replies(id,content,author(displayName,emailAddress),createdTime))", "includeDeleted": False}))


def read_document() -> None:
    doc = request_json("GET", f"{DOCS}/documents/{url_quote(env('DOCUMENT_ID', required=True))}", token=access_token(), params={"includeTabsContent": True, "suggestionsViewMode": "PREVIEW_WITHOUT_SUGGESTIONS"})
    print_json({"documentId": doc.get("documentId"), "title": doc.get("title"), "revisionId": doc.get("revisionId"), "tabs": [{"tabId": tab.get("tabProperties", {}).get("tabId"), "title": tab.get("tabProperties", {}).get("title"), "index": tab.get("tabProperties", {}).get("index"), "nestingLevel": tab.get("tabProperties", {}).get("nestingLevel"), "text": doc_tab_text(tab)} for tab in all_tabs(doc.get("tabs", []))]})


def replace_placeholders() -> None:
    doc_id = env("DOCUMENT_ID", required=True)
    doc = request_json("GET", f"{DOCS}/documents/{url_quote(doc_id)}", token=access_token(), params={"includeTabsContent": True, "suggestionsViewMode": "SUGGESTIONS_INLINE"})
    replacements = env_json("REPLACEMENTS_JSON", None)
    if replacements is None:
        replacements = {env("PLACEHOLDER", required=True): env("REPLACEMENT", required=True)}
    body = {"requests": [{"replaceAllText": {"containsText": {"text": key, "matchCase": True}, "replaceText": value}} for key, value in replacements.items()], "writeControl": {"requiredRevisionId": doc.get("revisionId")}}
    result = request_json("POST", f"{DOCS}/documents/{url_quote(doc_id)}:batchUpdate", token=access_token(), json_body=body)
    print_json({"documentId": result.get("documentId"), "replies": result.get("replies"), "writeControl": result.get("writeControl")})


def share_document() -> None:
    body = {"type": env("TYPE", required=True), "role": env("ROLE", required=True)}
    if env("EMAIL_ADDRESS", ""):
        body["emailAddress"] = env("EMAIL_ADDRESS")
    if env("DOMAIN", ""):
        body["domain"] = env("DOMAIN")
    print_json(request_json("POST", f"{DRIVE}/files/{url_quote(env('DOCUMENT_ID', required=True))}/permissions", token=access_token(), params={"supportsAllDrives": True, "sendNotificationEmail": env_bool("SEND_NOTIFICATION", True), "fields": "id,type,role,emailAddress,domain"}, json_body=body))


def trash_document() -> None:
    print_json(request_json("PATCH", f"{DRIVE}/files/{url_quote(env('DOCUMENT_ID', required=True))}", token=access_token(), params={"supportsAllDrives": True, "fields": "id,name,trashed"}, json_body={"trashed": True}))
