#!/usr/bin/env bash

: "${ACCESS_TOKEN:?ACCESS_TOKEN is required}"
: "${DOCUMENT_ID:?DOCUMENT_ID is required}"
curl -sS \
  -H "Authorization: Bearer $ACCESS_TOKEN" \
  "https://docs.googleapis.com/v1/documents/$DOCUMENT_ID?includeTabsContent=true&suggestionsViewMode=SUGGESTIONS_INLINE" \
  | jq --arg tab_id "${TAB_ID:-}" '
    def all_tabs:
      .[]? as $t | $t, ($t.childTabs | all_tabs);

    .tabs | all_tabs
    | select($tab_id == "" or .tabProperties.tabId == $tab_id)
    | {
        tabId: .tabProperties.tabId,
        title: .tabProperties.title,
        blocks: [
          .documentTab.body.content[]?
          | {
              startIndex,
              endIndex,
              text: ([.paragraph.elements[]?.textRun.content // empty] | join(""))
            }
        ]
      }'
