from __future__ import annotations

import csv
from pathlib import Path
from .google_api import *

SHEETS = "https://sheets.googleapis.com/v4"
DRIVE = "https://www.googleapis.com/drive/v3"


def sid() -> str:
    return env("SPREADSHEET_ID", required=True)


def append_rows() -> None:
    print_json(request_json("POST", f"{SHEETS}/spreadsheets/{url_quote(sid())}/values/{url_quote(env('RANGE', required=True))}:append", token=access_token(), params={"valueInputOption": env("VALUE_INPUT_OPTION", "USER_ENTERED"), "insertDataOption": env("INSERT_DATA_OPTION", "INSERT_ROWS"), "includeValuesInResponse": True}, json_body=env_json("BODY_JSON", required=True)))


def batch_update_formatting() -> None:
    print_json(request_json("POST", f"{SHEETS}/spreadsheets/{url_quote(sid())}:batchUpdate", token=access_token(), json_body=env_json("BODY_JSON", required=True)))


def clear_range() -> None:
    print_json(request_json("POST", f"{SHEETS}/spreadsheets/{url_quote(sid())}/values/{url_quote(env('RANGE', required=True))}:clear", token=access_token(), json_body={}))


def continue_spreadsheet_search() -> None:
    print_json(request_json("GET", f"{DRIVE}/files", token=access_token(), params={"q": env("QUERY", required=True), "pageToken": env("NEXT_PAGE_TOKEN", required=True), "pageSize": env_int("PAGE_SIZE", 20), "supportsAllDrives": True, "includeItemsFromAllDrives": True, "fields": "nextPageToken,files(id,name,webViewLink,modifiedTime,owners(emailAddress),mimeType)"}))


def create_developer_metadata() -> None:
    print_json(request_json("POST", f"{SHEETS}/spreadsheets/{url_quote(sid())}:batchUpdate", token=access_token(), json_body=env_json("BODY_JSON", required=True)))


def create_spreadsheet() -> None:
    result = request_json("POST", f"{SHEETS}/spreadsheets", token=access_token(), json_body=env_json("BODY_JSON", required=True))
    print_json({"spreadsheetId": result.get("spreadsheetId"), "spreadsheetUrl": result.get("spreadsheetUrl"), "title": result.get("properties", {}).get("title"), "sheets": [{"sheetId": sheet.get("properties", {}).get("sheetId"), "title": sheet.get("properties", {}).get("title")} for sheet in result.get("sheets", [])]})


def delete_sheet() -> None:
    body = {"requests": [{"deleteSheet": {"sheetId": env_int("SHEET_ID", 0)}}]}
    print_json(request_json("POST", f"{SHEETS}/spreadsheets/{url_quote(sid())}:batchUpdate", token=access_token(), json_body=body))


def export_sheet_csv() -> None:
    payload = request_json("GET", f"{SHEETS}/spreadsheets/{url_quote(sid())}/values/{url_quote(env('RANGE', required=True))}", token=access_token(), params={"majorDimension": "ROWS", "valueRenderOption": "FORMATTED_VALUE"})
    out = Path(env("OUT", required=True)).expanduser()
    out.parent.mkdir(parents=True, exist_ok=True)
    with out.open("w", newline="", encoding="utf-8") as handle:
        csv.writer(handle).writerows(payload.get("values", []))
    print_json({"out": str(out), "rows": len(payload.get("values", [])), "bytes": out.stat().st_size})


def export_spreadsheet() -> None:
    data = request_bytes("GET", f"{DRIVE}/files/{url_quote(sid())}/export", token=access_token(), params={"mimeType": env("MIME_TYPE", required=True)})
    result = write_bytes(env("OUT", required=True), data)
    result["spreadsheetId"] = sid()
    print_json(result)


def find_spreadsheets() -> None:
    print_json(request_json("GET", f"{DRIVE}/files", token=access_token(), params={"q": env("QUERY", "mimeType = 'application/vnd.google-apps.spreadsheet' and trashed = false"), "pageSize": env_int("PAGE_SIZE", 20), "supportsAllDrives": True, "includeItemsFromAllDrives": True, "fields": "nextPageToken,files(id,name,webViewLink,modifiedTime,owners(emailAddress),mimeType)"}))


def get_spreadsheet_structure() -> None:
    print_json(request_json("GET", f"{SHEETS}/spreadsheets/{url_quote(sid())}", token=access_token(), params={"includeGridData": False, "fields": "spreadsheetId,properties.title,spreadsheetUrl,sheets(properties(sheetId,title,index,gridProperties(rowCount,columnCount,frozenRowCount,frozenColumnCount)))"}))


def inspect_sharing() -> None:
    print_json(request_json("GET", f"{DRIVE}/files/{url_quote(sid())}", token=access_token(), params={"supportsAllDrives": True, "fields": "id,name,mimeType,webViewLink,owners(emailAddress),capabilities(canShare)"}))


def inspect_sheet_before_delete() -> None:
    print_json(request_json("GET", f"{SHEETS}/spreadsheets/{url_quote(sid())}", token=access_token(), params={"includeGridData": False, "fields": "properties.title,sheets(properties(sheetId,title,index,gridProperties(rowCount,columnCount)))"}))


def preview_range_clear() -> None:
    read_range()


def preview_range_write() -> None:
    read_range()


def read_multiple_ranges() -> None:
    ranges = env_json("RANGES_JSON", required=True)
    payload = request_json("GET", f"{SHEETS}/spreadsheets/{url_quote(sid())}/values:batchGet", token=access_token(), params={"ranges": ranges, "majorDimension": "ROWS", "valueRenderOption": "FORMATTED_VALUE"})
    print_json(payload.get("valueRanges", []))


def read_range() -> None:
    print_json(request_json("GET", f"{SHEETS}/spreadsheets/{url_quote(sid())}/values/{url_quote(env('RANGE', required=True))}", token=access_token(), params={"majorDimension": "ROWS", "valueRenderOption": "FORMATTED_VALUE"}))


def read_values_by_developer_metadata() -> None:
    print_json(request_json("POST", f"{SHEETS}/spreadsheets/{url_quote(sid())}/values:batchGetByDataFilter", token=access_token(), json_body=env_json("BODY_JSON", required=True)))


def search_developer_metadata() -> None:
    print_json(request_json("POST", f"{SHEETS}/spreadsheets/{url_quote(sid())}/developerMetadata:search", token=access_token(), json_body=env_json("BODY_JSON", required=True)))


def share_spreadsheet() -> None:
    body = {"type": env("TYPE", "user"), "role": env("ROLE", "reader"), "emailAddress": env("EMAIL", required=True)}
    print_json(request_json("POST", f"{DRIVE}/files/{url_quote(sid())}/permissions", token=access_token(), params={"sendNotificationEmail": env_bool("SEND_NOTIFICATION", True), "supportsAllDrives": True, "fields": "id,type,role,emailAddress"}, json_body=body))


def write_range() -> None:
    print_json(request_json("PUT", f"{SHEETS}/spreadsheets/{url_quote(sid())}/values/{url_quote(env('RANGE', required=True))}", token=access_token(), params={"valueInputOption": env("VALUE_INPUT_OPTION", "USER_ENTERED"), "includeValuesInResponse": True}, json_body=env_json("BODY_JSON", required=True)))
