#!/usr/bin/env bash

: "${ACCESS_TOKEN:?ACCESS_TOKEN is required}"
: "${PRESENTATION_ID:?PRESENTATION_ID is required}"
curl -sS -H "Authorization: Bearer $ACCESS_TOKEN" \
  "https://slides.googleapis.com/v1/presentations/$PRESENTATION_ID?fields=slides(objectId,slideProperties(notesPage(pageElements(objectId,shape(placeholder,text)))))" \
  | jq -r '
    .slides[] |
    {
      slideObjectId: .objectId,
      notes: (
        [.slideProperties.notesPage.pageElements[]?
          | select(.shape.placeholder.type == "BODY")
          | (.shape.text.textElements // [])
          | .[]?
          | .textRun.content // ""]
        | join("")
      )
    }'
