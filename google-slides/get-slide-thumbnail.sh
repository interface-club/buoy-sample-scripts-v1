#!/usr/bin/env bash

: "${ACCESS_TOKEN:?ACCESS_TOKEN is required}"
: "${PRESENTATION_ID:?PRESENTATION_ID is required}"
: "${PAGE_OBJECT_ID:?PAGE_OBJECT_ID is required}"
curl -sS -H "Authorization: Bearer $ACCESS_TOKEN" \
  "https://slides.googleapis.com/v1/presentations/$PRESENTATION_ID/pages/$PAGE_OBJECT_ID/thumbnail?thumbnailProperties.mimeType=PNG&thumbnailProperties.thumbnailSize=LARGE" \
  | jq -r '.contentUrl'
