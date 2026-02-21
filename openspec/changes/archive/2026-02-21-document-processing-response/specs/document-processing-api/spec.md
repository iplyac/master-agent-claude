## MODIFIED Requirements

### Requirement: Docling agent response returned to client
After uploading to GCS, the system SHALL call the docling agent's `POST /api/process-document` endpoint with the GCS URI and receive the extracted content. The response to the caller SHALL include `content`, `metadata`, `gcs_uri` (input), and `result_gcs_uri` (the GCS URI of the processed markdown output returned by docling, if present).

#### Scenario: Docling agent response returned to client with result_gcs_uri
- **WHEN** the docling agent returns HTTP 200 with `content`, `metadata`, and `result_gcs_uri`
- **THEN** the system returns `content`, `metadata`, `gcs_uri` (input document URI), and `result_gcs_uri` to the original caller

#### Scenario: Docling agent response returned without result_gcs_uri
- **WHEN** the docling agent returns HTTP 200 with `content` and `metadata` but no `result_gcs_uri`
- **THEN** the system returns `content`, `metadata`, and `gcs_uri`; `result_gcs_uri` is omitted or null

#### Scenario: Docling agent unavailable returns 503
- **WHEN** `DOCLING_AGENT_URL` is not configured
- **THEN** the system returns HTTP 503 with an error indicating the service is unavailable

#### Scenario: Docling agent error propagated
- **WHEN** the docling agent returns a non-200 response
- **THEN** the system returns HTTP 502 with a descriptive error message

#### Scenario: Docling agent timeout returns 504
- **WHEN** the docling agent does not respond within the configured timeout
- **THEN** the system returns HTTP 504
