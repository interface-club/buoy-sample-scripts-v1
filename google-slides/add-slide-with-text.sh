#!/usr/bin/env bash

: "${ACCESS_TOKEN:?ACCESS_TOKEN is required}"
: "${BODY_TEXT:?BODY_TEXT is required}"
: "${TITLE_TEXT:?TITLE_TEXT is required}"
: "${PRESENTATION_ID:?PRESENTATION_ID is required}"
SLIDE_ID="slide_$(date +%s)"
TITLE_BOX_ID="title_$(date +%s)"
BODY_BOX_ID="body_$(date +%s)"

REVISION_ID="$(curl -sS -H "Authorization: Bearer $ACCESS_TOKEN" \
  "https://slides.googleapis.com/v1/presentations/$PRESENTATION_ID?fields=revisionId" \
  | jq -r '.revisionId')"

BODY="$(jq -n \
  --arg rev "$REVISION_ID" \
  --arg slide "$SLIDE_ID" \
  --arg titleBox "$TITLE_BOX_ID" \
  --arg bodyBox "$BODY_BOX_ID" \
  --arg titleText "$TITLE_TEXT" \
  --arg bodyText "$BODY_TEXT" \
  '{
    requests: [
      { createSlide: { objectId: $slide, slideLayoutReference: { predefinedLayout: "BLANK" } } },
      {
        createShape: {
          objectId: $titleBox,
          shapeType: "TEXT_BOX",
          elementProperties: {
            pageObjectId: $slide,
            size: { width: { magnitude: 620, unit: "PT" }, height: { magnitude: 60, unit: "PT" } },
            transform: { scaleX: 1, scaleY: 1, translateX: 40, translateY: 40, unit: "PT" }
          }
        }
      },
      { insertText: { objectId: $titleBox, insertionIndex: 0, text: $titleText } },
      {
        createShape: {
          objectId: $bodyBox,
          shapeType: "TEXT_BOX",
          elementProperties: {
            pageObjectId: $slide,
            size: { width: { magnitude: 620, unit: "PT" }, height: { magnitude: 260, unit: "PT" } },
            transform: { scaleX: 1, scaleY: 1, translateX: 40, translateY: 120, unit: "PT" }
          }
        }
      },
      { insertText: { objectId: $bodyBox, insertionIndex: 0, text: $bodyText } }
    ],
    writeControl: { requiredRevisionId: $rev }
  }')"

curl -sS -X POST \
  -H "Authorization: Bearer $ACCESS_TOKEN" \
  -H "Content-Type: application/json" \
  --data "$BODY" \
  "https://slides.googleapis.com/v1/presentations/$PRESENTATION_ID:batchUpdate" \
  | jq .
