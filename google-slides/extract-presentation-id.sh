#!/usr/bin/env bash

: "${ACCESS_TOKEN:?ACCESS_TOKEN is required}"
: "${SLIDES_URL:?SLIDES_URL is required}"
PRESENTATION_ID="$(printf '%s' "$SLIDES_URL" | sed -E 's#.*presentation/d/([A-Za-z0-9_-]+).*#\1#')"
printf '%s\n' "$PRESENTATION_ID"
