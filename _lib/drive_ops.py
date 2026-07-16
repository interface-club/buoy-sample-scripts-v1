from __future__ import annotations

from .google_api import *

BASE = "https://www.googleapis.com/drive/v3"
UPLOAD = "https://www.googleapis.com/upload/drive/v3"


def copy_file() -> None:
    body = {"name": env("NEW_NAME", required=True), "parents": [env("PARENT_ID", "root")]}
    print_json(request_json("POST", f"{BASE}/files/{url_quote(env('FILE_ID', required=True))}/copy", token=access_token(), params={"supportsAllDrives": True, "fields": "id,name,webViewLink"}, json_body=body))


def create_folder() -> None:
    body = {"name": env("NAME", required=True), "mimeType": "application/vnd.google-apps.folder", "parents": [env("PARENT_ID", "root")]}
    print_json(request_json("POST", f"{BASE}/files", token=access_token(), params={"supportsAllDrives": True, "fields": "id,name,webViewLink"}, json_body=body))


def delete_file() -> None:
    file_id = env("FILE_ID", required=True)
    status, body, _ = request("DELETE", f"{BASE}/files/{url_quote(file_id)}", token=access_token(), params={"supportsAllDrives": True})
    print_json({"fileId": file_id, "status": status, "deleted": body == b""})


def download_file() -> None:
    file_id = env("FILE_ID", required=True)
    data = request_bytes("GET", f"{BASE}/files/{url_quote(file_id)}", token=access_token(), params={"alt": "media", "supportsAllDrives": True})
    result = write_bytes(env("OUT", required=True), data)
    result["fileId"] = file_id
    print_json(result)


def export_workspace_file() -> None:
    file_id = env("FILE_ID", required=True)
    data = request_bytes("GET", f"{BASE}/files/{url_quote(file_id)}/export", token=access_token(), params={"mimeType": env("MIME", required=True)})
    result = write_bytes(env("OUT", required=True), data)
    result["fileId"] = file_id
    print_json(result)


def get_file_metadata() -> None:
    fields = env("FIELDS", "id,name,mimeType,parents,driveId,owners(displayName,emailAddress),createdTime,modifiedTime,size,trashed,webViewLink,webContentLink,exportLinks,capabilities(canDownload,canEdit,canDelete,canShare)")
    print_json(request_json("GET", f"{BASE}/files/{url_quote(env('FILE_ID', required=True))}", token=access_token(), params={"supportsAllDrives": True, "fields": fields}))


def get_start_page_token() -> None:
    print_json(request_json("GET", f"{BASE}/changes/startPageToken", token=access_token(), params={"supportsAllDrives": True, "fields": "startPageToken"}))


def list_changes() -> None:
    print_json(request_json("GET", f"{BASE}/changes", token=access_token(), params={"pageToken": env("PAGE_TOKEN", required=True), "supportsAllDrives": True, "includeItemsFromAllDrives": True, "fields": "nextPageToken,newStartPageToken,changes(fileId,removed,time,file(id,name,mimeType,trashed,modifiedTime,webViewLink))"}))


def list_folder_contents() -> None:
    folder_id = env("FOLDER_ID", "root")
    query = env("QUERY", f"'{drive_query_literal(folder_id)}' in parents and trashed=false")
    payload = request_json("GET", f"{BASE}/files", token=access_token(), params={"q": query, "pageSize": env_int("PAGE_SIZE", 100), "supportsAllDrives": True, "includeItemsFromAllDrives": True, "fields": "nextPageToken,files(id,name,mimeType,modifiedTime,size,webViewLink)"})
    print_json(payload)


def list_permissions() -> None:
    print_json(request_json("GET", f"{BASE}/files/{url_quote(env('FILE_ID', required=True))}/permissions", token=access_token(), params={"supportsAllDrives": True, "fields": "permissions(id,type,role,emailAddress,domain,displayName,allowFileDiscovery,expirationTime,deleted)"}))


def list_shared_drives() -> None:
    params = {"pageSize": env_int("PAGE_SIZE", 100), "fields": "nextPageToken,drives(id,name,createdTime,hidden)"}
    if env("QUERY", ""):
        params["q"] = env("QUERY")
    if active_page_token():
        params["pageToken"] = active_page_token()
    print_json(request_json("GET", f"{BASE}/drives", token=access_token(), params=params))


def move_file() -> None:
    print_json(request_json("PATCH", f"{BASE}/files/{url_quote(env('FILE_ID', required=True))}", token=access_token(), params={"addParents": env("NEW_PARENT_ID", required=True), "removeParents": env("OLD_PARENT_ID", required=True), "supportsAllDrives": True, "fields": "id,name,parents,driveId,webViewLink"}))


def remove_permission() -> None:
    file_id = env("FILE_ID", required=True)
    permission_id = env("PERMISSION_ID", required=True)
    status, body, _ = request("DELETE", f"{BASE}/files/{url_quote(file_id)}/permissions/{url_quote(permission_id)}", token=access_token(), params={"supportsAllDrives": True})
    print_json({"fileId": file_id, "permissionId": permission_id, "status": status, "removed": body == b""})


def search_files() -> None:
    query = env("QUERY", "name contains 'invoice' and trashed=false")
    page_size = env_int("PAGE_SIZE", 50)
    params = {"q": query, "pageSize": page_size, "fields": "nextPageToken,incompleteSearch,files(id,name,mimeType,parents,driveId,modifiedTime,size,webViewLink,capabilities/canDownload)", "supportsAllDrives": True, "includeItemsFromAllDrives": True}
    if active_page_token():
        params["pageToken"] = active_page_token()
    payload = request_json("GET", f"{BASE}/files", token=access_token(), params=params)
    print_json(
        {
            "files": payload.get("files", []),
            "incompleteSearch": payload.get("incompleteSearch", False),
            "nextPageToken": payload.get("nextPageToken"),
        }
    )


def search_shared_drive() -> None:
    print_json(request_json("GET", f"{BASE}/files", token=access_token(), params={"corpora": "drive", "driveId": env("DRIVE_ID", required=True), "includeItemsFromAllDrives": True, "supportsAllDrives": True, "q": env("QUERY", "trashed=false"), "pageSize": env_int("PAGE_SIZE", 100), "fields": "nextPageToken,incompleteSearch,files(id,name,mimeType,parents,driveId,modifiedTime,webViewLink)"}))


def share_file_publicly() -> None:
    body = {"type": "anyone", "role": env("ROLE", "reader"), "allowFileDiscovery": env_bool("ALLOW_FILE_DISCOVERY", False)}
    print_json(request_json("POST", f"{BASE}/files/{url_quote(env('FILE_ID', required=True))}/permissions", token=access_token(), params={"supportsAllDrives": True, "fields": "id,type,role,allowFileDiscovery"}, json_body=body))


def share_file() -> None:
    body = {"type": env("TYPE", "user"), "role": env("ROLE", "reader"), "emailAddress": env("EMAIL", required=True)}
    print_json(request_json("POST", f"{BASE}/files/{url_quote(env('FILE_ID', required=True))}/permissions", token=access_token(), params={"supportsAllDrives": True, "sendNotificationEmail": env_bool("SEND_NOTIFICATION", True), "fields": "id,type,role,emailAddress"}, json_body=body))


def trash_file() -> None:
    print_json(request_json("PATCH", f"{BASE}/files/{url_quote(env('FILE_ID', required=True))}", token=access_token(), params={"supportsAllDrives": True, "fields": "id,name,trashed"}, json_body={"trashed": True}))


def update_file_metadata() -> None:
    body = env_json("BODY_JSON", None) or {"name": env("NEW_NAME", required=True)}
    print_json(request_json("PATCH", f"{BASE}/files/{url_quote(env('FILE_ID', required=True))}", token=access_token(), params={"supportsAllDrives": True, "fields": env("FIELDS", "id,name,modifiedTime,webViewLink")}, json_body=body))


def upload_small_file() -> None:
    local_path = Path(env("LOCAL_PATH", required=True)).expanduser()
    name = env("NAME", local_path.name)
    mime = env("MIME", guess_mime(str(local_path)))
    parent_id = env("PARENT_ID", "root")
    boundary = f"buoy_boundary_{int(time.time())}"
    metadata = json.dumps({"name": name, "parents": [parent_id]}, separators=(",", ":")).encode()
    content = local_path.read_bytes()
    body = b"".join([
        f"--{boundary}\r\nContent-Type: application/json; charset=UTF-8\r\n\r\n".encode(), metadata,
        f"\r\n--{boundary}\r\nContent-Type: {mime}\r\n\r\n".encode(), content,
        f"\r\n--{boundary}--\r\n".encode(),
    ])
    print_json(request_json("POST", f"{UPLOAD}/files", token=access_token(), params={"uploadType": "multipart", "supportsAllDrives": True, "fields": "id,name,webViewLink"}, headers={"Content-Type": f"multipart/related; boundary={boundary}"}, data=body))


def resumable_upload() -> None:
    local_path = Path(env("LOCAL_PATH", required=True)).expanduser()
    name = env("NAME", local_path.name)
    mime = env("MIME", guess_mime(str(local_path)))
    size = local_path.stat().st_size
    _, _, headers = request("POST", f"{UPLOAD}/files", token=access_token(), params={"uploadType": "resumable", "supportsAllDrives": True, "fields": "id,name,webViewLink"}, json_body={"name": name, "parents": [env("PARENT_ID", "root")]}, headers={"X-Upload-Content-Type": mime, "X-Upload-Content-Length": str(size)}, accept=(200, 201))
    session_url = headers.get("Location")
    if not session_url:
        fail("Google did not return a resumable upload session URL")
    print_json(request_json("PUT", session_url, headers={"Content-Type": mime, "Content-Length": str(size)}, data=local_path.read_bytes()))
