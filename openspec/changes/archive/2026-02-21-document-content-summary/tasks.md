## 1. master-agent: Gemini summarization

- [x] 1.1 Add `summarize_document(content: str) -> Optional[str]` to `MediaClient` in `agent/media_client.py` — truncate content at 30 000 chars, call Gemini with a prompt asking for a 2-4 sentence plain-text summary, return None on any exception (log warning)
- [x] 1.2 Add `summary: Optional[str] = None` to `DocumentResponse` in `agent/models.py`
- [x] 1.3 In `app.py` `/api/document` handler, after docling succeeds, call `media_client.summarize_document(content)` and pass the result to `DocumentResponse`

## 2. telegram-bot: show summary in message

- [x] 2.1 In `tgbot/handlers/document.py`, append the `summary` field from the response to the processing summary message when present (after stats, before sending the file)

## 3. Tests

- [x] 3.1 Add unit tests for `MediaClient.summarize_document` in master-agent: success case, Gemini exception → returns None, empty content → returns None without calling Gemini
- [x] 3.2 Update `tests/test_document_api.py` to assert `summary` is included in the response when `media_client.summarize_document` returns a value, and null when it returns None
- [x] 3.3 Update `tests/test_document_handler.py` in telegram-bot: assert summary is included in the text message when present in response, and absent when null
