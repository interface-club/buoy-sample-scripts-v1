#!/usr/bin/env bash

: "${ACCESS_TOKEN:?ACCESS_TOKEN is required}"
: "${PRESENTATION_ID:?PRESENTATION_ID is required}"
: "${SLIDE_OBJECT_ID:?SLIDE_OBJECT_ID is required}"
: "${IMAGE_URL:?IMAGE_URL is required}"
IMAGE_OBJECT_ID="image_$(date +%s)"

REVISION_ID="$(curl -sS -H "Authorization: Bearer $ACCESS_TOKEN" \
  "https://slides.googleapis.com/v1/presentations/$PRESENTATION_ID?fields=revisionId" \
  | jq -r '.revisionId')"

BODY="$(jq -n \
  --arg rev "$REVISION_ID" \
  --arg slide "$SLIDE_OBJECT_ID" \
  --arg imageId "$IMAGE_OBJECT_ID" \
  --arg url "$IMAGE_URL" \
  '{
    requests: [
      {
        createImage: {
          objectId: $imageId,
          url: $url,
          elementProperties: {
            pageObjectId: $slide,
            size: { width: { magnitude: 320, unit: "PT" }, height: { magnitude: 180, unit: "PT" } },
            transform: { scaleX: 1, scaleY: 1, translateX: 360, translateY: 160, unit: "PT" }
          }
        }
      }
    ],
    writeControl: { requiredRevisionId: $rev }
  }')"

curl -sS -X POST \
  -H "Authorization: Bearer $ACCESS_TOKEN" \
  -H "Content-Type: application/json" \
  --data "$BODY" \
  "https://slides.googleapis.com/v1/presentations/$PRESENTATION_ID:batchUpdate" \
  | jq .
