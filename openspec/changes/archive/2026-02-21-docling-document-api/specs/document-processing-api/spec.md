## ADDED Requirements

### Requirement: Accept document from Telegram bot
The system SHALL expose a `POST /api/document` endpoint that accepts a base64-encoded document with conversation context and optional Telegram metadata.

#### Scenario: Valid document accepted
- **WHEN** a client sends a POST request to `/api/document` with `conversation_id`, `document_base64`, `mime_type`, and `filename`
- **THEN** the system returns HTTP 200 with `content` (extracted text) and `metadata`

#### Scenario: Missing document_base64 returns 400
- **WHEN** a client sends a POST request without `document_base64`
- **THEN** the system returns HTTP 400 with a descriptive error message

#### Scenario: Missing conversation_id returns 400
- **WHEN** a client sends a POST request without `conversation_id`
- **THEN** the system returns HTTP 400 with a descriptive error message

#### Scenario: Unsupported mime_type returns 400
- **WHEN** a client sends a document with an unsupported MIME type (e.g. `image/bmp`)
- **THEN** the system returns HTTP 400 indicating the MIME type is not supported

#### Scenario: Invalid base64 returns 400
- **WHEN** a client sends malformed base64 in `document_base64`
- **THEN** the system returns HTTP 400 indicating invalid encoding

### Requirement: Upload document to GCS before processing
Before calling the docling agent, the system SHALL upload the raw document bytes to `gs://docling-documents/input/{conversation_id}/{timestamp_ms}_{filename}`.

#### Scenario: Document uploaded to GCS input folder
- **WHEN** a valid document is received
- **THEN** the document is stored at `gs://docling-documents/input/{conversation_id}/{timestamp_ms}_{filename}` before the docling agent is called

#### Scenario: GCS upload failure returns 500
- **WHEN** the GCS upload fails (permissions, network, quota)
- **THEN** the system returns HTTP 500 and does NOT call the docling agent

### Requirement: Delegate document processing to docling agent
After uploading to GCS, the system SHALL call the docling agent's `POST /api/process-document` endpoint with the GCS URI and receive the extracted content.

#### Scenario: Docling agent called with GCS URI
- **WHEN** the document is successfully uploaded to GCS
- **THEN** the system sends `{"document_url": "gs://docling-documents/input/..."}` to the docling agent URL

#### Scenario: Docling agent response returned to client
- **WHEN** the docling agent returns HTTP 200 with `content` and `metadata`
- **THEN** the system returns the `content` and `metadata` to the original caller

#### Scenario: Docling agent unavailable returns 503
- **WHEN** `DOCLING_AGENT_URL` is not configured
- **THEN** the system returns HTTP 503 with an error indicating the service is unavailable

#### Scenario: Docling agent error propagated
- **WHEN** the docling agent returns a non-200 response
- **THEN** the system returns HTTP 502 with a descriptive error message

#### Scenario: Docling agent timeout returns 504
- **WHEN** the docling agent does not respond within the configured timeout
- **THEN** the system returns HTTP 504

### Requirement: Authenticated calls to docling agent
The system SHALL authenticate requests to the docling agent using Google Cloud ID tokens when the agent URL is a Cloud Run service (non-localhost).

#### Scenario: ID token added to Cloud Run call
- **WHEN** `DOCLING_AGENT_URL` points to a Cloud Run service (https://...)
- **THEN** the outgoing request includes `Authorization: Bearer <id_token>` with audience set to `DOCLING_AGENT_URL`

#### Scenario: No auth for localhost development
- **WHEN** `DOCLING_AGENT_URL` contains `localhost` or `127.0.0.1`
- **THEN** the outgoing request is sent without an Authorization header

### Requirement: Supported document MIME types
The system SHALL accept the following MIME types for documents: `application/pdf`, `application/vnd.openxmlformats-officedocument.wordprocessingml.document` (DOCX), `application/vnd.openxmlformats-officedocument.presentationml.presentation` (PPTX), `application/vnd.openxmlformats-officedocument.spreadsheetml.sheet` (XLSX), `text/html`, `text/markdown`, `text/csv`, `image/png`, `image/jpeg`, `image/tiff`, `image/bmp`, `image/webp`.

#### Scenario: PDF accepted
- **WHEN** a document with mime_type `application/pdf` is submitted
- **THEN** the system accepts and processes it

#### Scenario: Unsupported type rejected
- **WHEN** a document with mime_type `audio/mpeg` is submitted
- **THEN** the system returns HTTP 400
