#!/usr/bin/env bash

: "${ACCESS_TOKEN:?ACCESS_TOKEN is required}"
: "${DOCUMENT_ID:?DOCUMENT_ID is required}"
curl -sS \
  -H "Authorization: Bearer $ACCESS_TOKEN" \
  "https://docs.googleapis.com/v1/documents/$DOCUMENT_ID?includeTabsContent=true&suggestionsViewMode=PREVIEW_WITHOUT_SUGGESTIONS" \
  | jq '
    def all_tabs:
      .[]? as $t | $t, ($t.childTabs | all_tabs);

    {
      documentId,
      title,
      revisionId,
      tabs: [
        .tabs | all_tabs | {
          tabId: .tabProperties.tabId,
          title: .tabProperties.title,
          index: .tabProperties.index,
          nestingLevel: .tabProperties.nestingLevel,
          text: ([.documentTab.body.content[]?
            | .paragraph.elements[]?.textRun.content // empty] | join(""))
        }
      ]
    }'
