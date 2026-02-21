## MODIFIED Requirements

### Requirement: Document messages are forwarded to master-agent
The system SHALL handle Telegram messages that contain a document attachment. Upon receiving such a message, the bot SHALL download the file from Telegram, base64-encode it, and forward it to the master-agent `/api/document` endpoint along with the filename, MIME type, conversation ID, and Telegram metadata. On success, the bot SHALL reply with a formatted processing-details message and send the extracted content as a `.md` file attachment.

#### Scenario: User sends a PDF document — success with details and file
- **WHEN** a user sends a PDF file as a Telegram document message
- **THEN** the bot downloads the file, POSTs to master-agent `/api/document`, and on HTTP 200:
  - sends a text message summarising processing metadata (filename, pages, tables found, images found, processing time)
  - sends a follow-up Telegram document with the extracted content as `<filename>.md`

#### Scenario: User sends a DOCX document
- **WHEN** a user sends a `.docx` file as a Telegram document message
- **THEN** the bot forwards it to master-agent with the correct MIME type and replies with a formatted summary and `.md` attachment

#### Scenario: User sends a document with no recognised MIME type
- **WHEN** Telegram reports `document.mime_type` as `None` or an empty string
- **THEN** the bot uses `"application/octet-stream"` as the MIME type and proceeds normally

## ADDED Requirements

### Requirement: Processing summary message is formatted
After a successful document processing response, the system SHALL send a formatted text message to the user that includes: the original filename, the number of pages (if available), the number of tables found (if available), the number of images found (if available), and the processing time in seconds (if available). Fields not present in the metadata SHALL be omitted from the summary.

#### Scenario: Full metadata available
- **WHEN** master-agent returns metadata with pages=12, tables_found=3, images_found=5, processing_time_ms=15400
- **THEN** the bot sends a message such as:
  ```
  Document processed: report.pdf
  Pages: 12 | Tables: 3 | Images: 5
  Processing time: 15.4s
  ```

#### Scenario: Partial metadata available
- **WHEN** master-agent returns metadata with only pages=5 and no tables_found or images_found
- **THEN** the bot sends a summary showing pages only, omitting missing fields

#### Scenario: No metadata returned
- **WHEN** master-agent returns no metadata
- **THEN** the bot sends a minimal summary with only the filename

### Requirement: Extracted content is sent as a Markdown file attachment
After sending the processing summary, the system SHALL send the `content` field from the master-agent response as a `.md` file via Telegram's `send_document` API. The filename SHALL be derived from the original document filename with the extension replaced by `.md`.

#### Scenario: Markdown file sent after summary
- **WHEN** master-agent returns `content` with markdown text
- **THEN** the bot sends the content as an in-memory `.md` file attachment; the filename is `<original_basename>.md`

#### Scenario: Empty content
- **WHEN** master-agent returns an empty `content` string
- **THEN** the bot skips sending the file attachment and includes a note in the summary message indicating no content was extracted
