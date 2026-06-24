#!/usr/bin/env bash

: "${ACCESS_TOKEN:?ACCESS_TOKEN is required}"
: "${PRESENTATION_ID:?PRESENTATION_ID is required}"
: "${OBJECT_ID:?OBJECT_ID is required}"
curl -sS -H "Authorization: Bearer $ACCESS_TOKEN" \
  "https://slides.googleapis.com/v1/presentations/$PRESENTATION_ID?fields=title,revisionId,slides(objectId,pageElements(objectId,shape(text)))" \
  | jq --arg id "$OBJECT_ID" '
    {
      title,
      revisionId,
      matchingSlides: [.slides[] | select(.objectId == $id) | {slideObjectId:.objectId}],
      matchingElements: [
        .slides[] as $s
        | ($s.pageElements // [])[]
        | select(.objectId == $id)
        | {slideObjectId:$s.objectId, objectId, text: ((.shape.text.textElements // []) | map(.textRun.content // "") | join(""))}
      ]
    }'
