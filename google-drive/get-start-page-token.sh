#!/usr/bin/env bash

: "${ACCESS_TOKEN:?ACCESS_TOKEN is required}"
curl -sS \
  -H "Authorization: Bearer $ACCESS_TOKEN" \
  "https://www.googleapis.com/drive/v3/changes/startPageToken?supportsAllDrives=true&fields=startPageToken" \
| jq -r '.startPageToken'
