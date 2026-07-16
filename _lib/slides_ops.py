from __future__ import annotations

import re
import time
from .google_api import *

SLIDES = "https://slides.googleapis.com/v1"
DRIVE = "https://www.googleapis.com/drive/v3"


def pid() -> str:
    return env("PRESENTATION_ID", required=True)


def revision_id(presentation_id: str) -> str:
    return request_json("GET", f"{SLIDES}/presentations/{url_quote(presentation_id)}", token=access_token(), params={"fields": "revisionId"}).get("revisionId")


def batch_update(presentation_id: str, body: dict[str, Any]) -> Any:
    return request_json("POST", f"{SLIDES}/presentations/{url_quote(presentation_id)}:batchUpdate", token=access_token(), json_body=body)


def add_image() -> None:
    presentation_id = pid()
    image_id = env("IMAGE_OBJECT_ID", f"image_{int(time.time())}")
    body = {
        "requests": [
            {
                "createImage": {
                    "objectId": image_id,
                    "url": env("IMAGE_URL", required=True),
                    "elementProperties": {
                        "pageObjectId": env("SLIDE_OBJECT_ID", required=True),
                        "size": {
                            "width": {"magnitude": float(env("WIDTH_PT", "320")), "unit": "PT"},
                            "height": {"magnitude": float(env("HEIGHT_PT", "180")), "unit": "PT"},
                        },
                        "transform": {
                            "scaleX": 1,
                            "scaleY": 1,
                            "translateX": float(env("X_PT", "360")),
                            "translateY": float(env("Y_PT", "160")),
                            "unit": "PT",
                        },
                    },
                }
            }
        ],
        "writeControl": {"requiredRevisionId": revision_id(presentation_id)},
    }
    print_json(batch_update(presentation_id, body))


def add_slide_with_text() -> None:
    presentation_id = pid()
    stamp = int(time.time())
    slide_id = env("SLIDE_ID", f"slide_{stamp}")
    title_box = env("TITLE_BOX_ID", f"title_{stamp}")
    body_box = env("BODY_BOX_ID", f"body_{stamp}")
    body = {"requests": [{"createSlide": {"objectId": slide_id, "slideLayoutReference": {"predefinedLayout": env("LAYOUT", "BLANK")}}}, {"createShape": {"objectId": title_box, "shapeType": "TEXT_BOX", "elementProperties": {"pageObjectId": slide_id, "size": {"width": {"magnitude": 620, "unit": "PT"}, "height": {"magnitude": 60, "unit": "PT"}}, "transform": {"scaleX": 1, "scaleY": 1, "translateX": 40, "translateY": 40, "unit": "PT"}}}}, {"insertText": {"objectId": title_box, "insertionIndex": 0, "text": env("TITLE_TEXT", required=True)}}, {"createShape": {"objectId": body_box, "shapeType": "TEXT_BOX", "elementProperties": {"pageObjectId": slide_id, "size": {"width": {"magnitude": 620, "unit": "PT"}, "height": {"magnitude": 260, "unit": "PT"}}, "transform": {"scaleX": 1, "scaleY": 1, "translateX": 40, "translateY": 120, "unit": "PT"}}}}, {"insertText": {"objectId": body_box, "insertionIndex": 0, "text": env("BODY_TEXT", required=True)}}], "writeControl": {"requiredRevisionId": revision_id(presentation_id)}}
    print_json(batch_update(presentation_id, body))


def copy_template() -> None:
    body = {"name": env("NEW_TITLE", required=True)}
    if env("DEST_FOLDER_ID", "") and env("DEST_FOLDER_ID") != "OPTIONAL_FOLDER_ID":
        body["parents"] = [env("DEST_FOLDER_ID")]
    print_json(request_json("POST", f"{DRIVE}/files/{url_quote(env('TEMPLATE_ID', required=True))}/copy", token=access_token(), params={"supportsAllDrives": True, "fields": "id,name,webViewLink"}, json_body=body))


def create_presentation() -> None:
    result = request_json("POST", f"{SLIDES}/presentations", token=access_token(), json_body={"title": env("TITLE", required=True)})
    print_json({"presentationId": result.get("presentationId"), "title": result.get("title")})


def delete_object() -> None:
    presentation_id = pid()
    body = {"requests": [{"deleteObject": {"objectId": env("OBJECT_ID", required=True)}}], "writeControl": {"requiredRevisionId": env("REVISION_ID", required=True)}}
    print_json(batch_update(presentation_id, body))


def export_presentation_pdf() -> None:
    data = request_bytes("GET", f"{DRIVE}/files/{url_quote(pid())}/export", token=access_token(), params={"mimeType": "application/pdf"})
    print_json(write_bytes(env("OUT", required=True), data))


def export_presentation_pptx() -> None:
    data = request_bytes("GET", f"{DRIVE}/files/{url_quote(pid())}/export", token=access_token(), params={"mimeType": "application/vnd.openxmlformats-officedocument.presentationml.presentation"})
    print_json(write_bytes(env("OUT", required=True), data))


def extract_presentation_id() -> None:
    url = env("SLIDES_URL", required=True)
    match = re.search(r"presentation/d/([A-Za-z0-9_-]+)", url)
    print_json({"presentationId": match.group(1) if match else url})


def find_presentations_in_folder() -> None:
    folder_id = drive_query_literal(env("FOLDER_ID", required=True))
    query = f"'{folder_id}' in parents and mimeType='application/vnd.google-apps.presentation' and trashed=false"
    print_json(request_json("GET", f"{DRIVE}/files", token=access_token(), params={"q": query, "pageSize": env_int("PAGE_SIZE", 100), "supportsAllDrives": True, "includeItemsFromAllDrives": True, "fields": "nextPageToken,files(id,name,webViewLink,modifiedTime)"}))


def find_presentations() -> None:
    text = drive_query_literal(env("QUERY_TEXT", required=True))
    query = f"mimeType='application/vnd.google-apps.presentation' and trashed=false and name contains '{text}'"
    params = {"q": query, "pageSize": env_int("PAGE_SIZE", 20), "supportsAllDrives": True, "includeItemsFromAllDrives": True, "fields": "nextPageToken,files(id,name,webViewLink,modifiedTime,owners(displayName,emailAddress),driveId)"}
    if active_page_token():
        params["pageToken"] = active_page_token()
    print_json(request_json("GET", f"{DRIVE}/files", token=access_token(), params=params))


def get_slide_thumbnail() -> None:
    result = request_json("GET", f"{SLIDES}/presentations/{url_quote(pid())}/pages/{url_quote(env('PAGE_OBJECT_ID', required=True))}/thumbnail", token=access_token(), params={"thumbnailProperties.mimeType": "PNG", "thumbnailProperties.thumbnailSize": "LARGE"})
    print_json({"contentUrl": result.get("contentUrl")})


def inspect_object_before_delete() -> None:
    object_id = env("OBJECT_ID", required=True)
    deck = request_json("GET", f"{SLIDES}/presentations/{url_quote(pid())}", token=access_token(), params={"fields": "title,revisionId,slides(objectId,pageElements(objectId,shape(text)))"})
    matching_slides = []
    matching_elements = []
    for slide in deck.get("slides", []) or []:
        if slide.get("objectId") == object_id:
            matching_slides.append({"slideObjectId": slide.get("objectId")})
        for element in slide.get("pageElements", []) or []:
            if element.get("objectId") == object_id:
                matching_elements.append({"slideObjectId": slide.get("objectId"), "objectId": object_id, "text": slide_text(element.get("shape"))})
    print_json({"title": deck.get("title"), "revisionId": deck.get("revisionId"), "matchingSlides": matching_slides, "matchingElements": matching_elements})


def read_presentation_outline() -> None:
    deck = request_json("GET", f"{SLIDES}/presentations/{url_quote(pid())}", token=access_token(), params={"fields": "presentationId,title,revisionId,pageSize,slides(objectId,slideProperties(notesPage),pageElements(objectId,shape(shapeType,placeholder,text),image,table,video,line,sheetsChart))"})
    slides = []
    for slide in deck.get("slides", []) or []:
        elements = []
        for element in slide.get("pageElements", []) or []:
            kind = "shape" if element.get("shape") else "image" if element.get("image") else "table" if element.get("table") else "video" if element.get("video") else "line" if element.get("line") else "sheetsChart" if element.get("sheetsChart") else "other"
            shape = element.get("shape") or {}
            elements.append({"objectId": element.get("objectId"), "kind": kind, "placeholder": (shape.get("placeholder") or {}).get("type"), "text": slide_text(shape).rstrip("\n")})
        notes = (((slide.get("slideProperties") or {}).get("notesPage") or {}).get("notesProperties") or {}).get("speakerNotesObjectId")
        slides.append({"slideObjectId": slide.get("objectId"), "notesPageObjectId": notes, "elements": elements})
    print_json({"presentationId": deck.get("presentationId"), "title": deck.get("title"), "revisionId": deck.get("revisionId"), "slides": slides})


def read_speaker_notes() -> None:
    deck = request_json("GET", f"{SLIDES}/presentations/{url_quote(pid())}", token=access_token(), params={"fields": "slides(objectId,slideProperties(notesPage(pageElements(objectId,shape(placeholder,text)))))"})
    rows = []
    for slide in deck.get("slides", []) or []:
        notes = []
        notes_page = ((slide.get("slideProperties") or {}).get("notesPage") or {})
        for element in notes_page.get("pageElements", []) or []:
            shape = element.get("shape") or {}
            if (shape.get("placeholder") or {}).get("type") == "BODY":
                notes.append(slide_text(shape))
        rows.append({"slideObjectId": slide.get("objectId"), "notes": "".join(notes)})
    print_json(rows)


def replace_placeholders() -> None:
    presentation_id = pid()
    replacements = env_json("REPLACEMENTS_JSON", required=True)
    body = {"requests": [{"replaceAllText": {"containsText": {"text": key, "matchCase": True}, "replaceText": value}} for key, value in replacements.items()], "writeControl": {"requiredRevisionId": revision_id(presentation_id)}}
    print_json(batch_update(presentation_id, body))


def share_presentation_publicly() -> None:
    body = {"type": "anyone", "role": env("ROLE", "reader"), "allowFileDiscovery": env_bool("ALLOW_FILE_DISCOVERY", False)}
    print_json(request_json("POST", f"{DRIVE}/files/{url_quote(pid())}/permissions", token=access_token(), params={"supportsAllDrives": True, "fields": "id,type,role,allowFileDiscovery"}, json_body=body))


def share_presentation() -> None:
    body = {"type": "user", "role": env("ROLE", "reader"), "emailAddress": env("EMAIL", required=True)}
    print_json(request_json("POST", f"{DRIVE}/files/{url_quote(pid())}/permissions", token=access_token(), params={"supportsAllDrives": True, "sendNotificationEmail": env_bool("SEND_NOTIFICATION", True), "fields": "id,type,role,emailAddress"}, json_body=body))


def update_speaker_notes() -> None:
    presentation_id = pid()
    body = {"requests": [{"deleteText": {"objectId": env("SPEAKER_NOTES_OBJECT_ID", required=True), "textRange": {"type": "ALL"}}}, {"insertText": {"objectId": env("SPEAKER_NOTES_OBJECT_ID"), "insertionIndex": 0, "text": env("NEW_NOTES", required=True)}}], "writeControl": {"requiredRevisionId": revision_id(presentation_id)}}
    print_json(batch_update(presentation_id, body))
