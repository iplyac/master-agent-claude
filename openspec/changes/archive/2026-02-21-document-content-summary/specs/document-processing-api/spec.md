## ADDED Requirements

### Requirement: Generate AI summary of extracted document content
After docling processing succeeds, the system SHALL call Gemini to generate a brief plain-text description (2-4 sentences) of the extracted markdown content and include it as `summary` in `DocumentResponse`. If summarization fails for any reason, the system SHALL proceed without `summary` (null) and log a warning.

#### Scenario: Summarization succeeds
- **WHEN** docling returns non-empty `content` and Gemini summarization succeeds
- **THEN** the response includes a non-empty `summary` string alongside `content`, `metadata`, `gcs_uri`, and `result_gcs_uri`

#### Scenario: Summarization fails gracefully
- **WHEN** the Gemini summarization call raises an exception (quota, network, model error)
- **THEN** the system logs a warning and returns the response with `summary` set to null; the document processing result is not affected

#### Scenario: Empty content skips summarization
- **WHEN** docling returns an empty `content` string
- **THEN** `summary` is null and no Gemini call is made
