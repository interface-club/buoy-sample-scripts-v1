#!/usr/bin/env bash

: "${ACCESS_TOKEN:?ACCESS_TOKEN is required}"
: "${PRESENTATION_ID:?PRESENTATION_ID is required}"
curl -sS -H "Authorization: Bearer $ACCESS_TOKEN" \
  "https://slides.googleapis.com/v1/presentations/$PRESENTATION_ID?fields=presentationId,title,revisionId,pageSize,slides(objectId,slideProperties(notesPage),pageElements(objectId,shape(shapeType,placeholder,text),image,table,video,line,sheetsChart))" \
  | jq '{
      presentationId,
      title,
      revisionId,
      slides: [
        .slides[] | {
          slideObjectId: .objectId,
          notesPageObjectId: .slideProperties.notesPage.notesProperties.speakerNotesObjectId,
          elements: [
            (.pageElements // [])[] | {
              objectId,
              kind: (if .shape then "shape" elif .image then "image" elif .table then "table" elif .video then "video" elif .line then "line" elif .sheetsChart then "sheetsChart" else "other" end),
              placeholder: .shape.placeholder.type,
              text: ((.shape.text.textElements // []) | map(.textRun.content // "") | join("") | gsub("\n$"; ""))
            }
          ]
        }
      ]
    }'
