#!/usr/bin/env bash

: "${ACCESS_TOKEN:?ACCESS_TOKEN is required}"
: "${DOC_URL:?DOC_URL is required}"
DOCUMENT_ID="$(printf '%s' "$DOC_URL" | sed -E 's#.*docs.google.com/document/d/([^/]+).*#\1#')"
printf '%s\n' "$DOCUMENT_ID"
