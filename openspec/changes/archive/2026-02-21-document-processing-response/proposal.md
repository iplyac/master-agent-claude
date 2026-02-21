## Why

When a user sends a document to the Telegram bot, they receive only a plain-text reply with the extracted content. The docling agent already returns rich metadata (page count, tables, images, processing time) and a GCS URI to the processed markdown file — none of this is surfaced to the user. The bot should present processing details and deliver the markdown as a file attachment, making document processing results immediately useful.

## What Changes

- Telegram bot formats a processing summary message (pages, tables, images found, processing time) after document processing completes
- Telegram bot sends the extracted content as a `.md` file attachment (built from the `content` field already in the response — no extra GCS download needed)
- Master-agent passes `result_gcs_uri` from the docling response through `DocumentResponse` so callers have the reference
- Text reply is replaced by: formatted summary message + document attachment

## Capabilities

### New Capabilities

_(none — this change modifies existing capabilities only)_

### Modified Capabilities

- `document-processing-api`: `DocumentResponse` must include `result_gcs_uri` (the GCS URI of the processed markdown output returned by docling)
- `document-handler`: response handling changes — send a formatted processing-details message and a `.md` file attachment instead of a plain text reply

## Impact

- `master-agent`: `agent/models.py` (`DocumentResponse`), `app.py` (`/api/document` handler)
- `telegram-bot`: `tgbot/handlers/document.py`
- No changes to docling agent, GCS clients, or API contracts between telegram-bot and master-agent beyond the addition of `result_gcs_uri`
