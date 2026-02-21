## Why

After document processing the user receives metadata stats and a `.md` file, but no indication of what the document actually contains. A brief AI-generated summary (2-4 sentences) gives immediate context before opening the file.

## What Changes

- Master-agent calls Gemini after docling processing to generate a short description of the extracted markdown content
- `DocumentResponse` gains a `summary: Optional[str]` field
- Telegram bot appends the summary to the processing details message (between stats and file attachment)
- If Gemini summarization fails, the response proceeds without summary (non-blocking)

## Capabilities

### New Capabilities

_(none)_

### Modified Capabilities

- `document-processing-api`: `DocumentResponse` gains optional `summary` field; `/api/document` generates it via Gemini after docling succeeds
- `document-handler`: processing summary message includes the AI-generated document description when present

## Impact

- `master-agent`: `agent/models.py`, `agent/media_client.py` (new method), `app.py`
- `telegram-bot`: `tgbot/handlers/document.py`
- No changes to docling agent, GCS, or API contracts between services beyond the additive `summary` field
