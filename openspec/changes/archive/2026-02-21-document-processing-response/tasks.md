## 1. master-agent: pass result_gcs_uri through DocumentResponse

- [x] 1.1 Add `result_gcs_uri: Optional[str] = None` field to `DocumentResponse` in `agent/models.py`
- [x] 1.2 In `app.py` `/api/document` handler, extract `result_gcs_uri` from docling result dict and pass it to `DocumentResponse`

## 2. telegram-bot: format processing summary and send MD attachment

- [x] 2.1 In `tgbot/handlers/document.py`, replace plain `reply_text(response_text)` with a formatted processing summary built from `result.get("metadata", {})` and the original filename
- [x] 2.2 After sending the summary, if `result.get("response")` is non-empty, send it as an in-memory `.md` file attachment using `update.message.reply_document()` — filename derived as `<basename>.md`
- [x] 2.3 If `result.get("response")` is empty, include a note in the summary that no content was extracted (skip file send)

## 3. Tests

- [x] 3.1 Update `tests/test_document_api.py` in master-agent to assert `result_gcs_uri` is present in the response when returned by docling
- [x] 3.2 Add/update document handler tests in telegram-bot to assert: summary message sent, `.md` document sent, correct filenames and metadata fields used
