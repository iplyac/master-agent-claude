### Requirement: Upload original image to GCS
When an image is received by the agent, the system SHALL save the original image bytes to the `upload/` folder of the configured GCS bucket before or during processing.

#### Scenario: Original image saved on receipt
- **WHEN** a user sends an image via the image API endpoint
- **THEN** the original image is uploaded to `gs://master-agent-images/upload/{session_id}/{timestamp_ms}.{ext}`

#### Scenario: GCS failure does not block response
- **WHEN** the GCS upload of the original image fails (network error, permission denied, etc.)
- **THEN** the system logs the error and continues processing, returning a normal response to the user

#### Scenario: No GCS client configured
- **WHEN** the `GCS_BUCKET_NAME` environment variable is not set
- **THEN** the system skips GCS upload entirely and processes the image normally

### Requirement: Upload processed image to GCS
When the image processing model returns an output image, the system SHALL save it to the `processed/` folder of the configured GCS bucket.

#### Scenario: Processed image saved after model output
- **WHEN** a user sends an image with a prompt and the model returns a processed image
- **THEN** the processed image is uploaded to `gs://master-agent-images/processed/{session_id}/{timestamp_ms}.{ext}`

#### Scenario: No processed image returned
- **WHEN** the model processes an image but returns only text (no output image)
- **THEN** no file is written to the `processed/` folder

#### Scenario: GCS failure for processed image does not block response
- **WHEN** the GCS upload of the processed image fails
- **THEN** the system logs the error and the processed image data is still returned to the caller normally

### Requirement: GCS object naming convention
The system SHALL name GCS objects using the pattern `{folder}/{session_id}/{unix_timestamp_ms}.{ext}` where `ext` is derived from the image MIME type.

#### Scenario: MIME type mapped to extension
- **WHEN** an image with MIME type `image/jpeg` is uploaded
- **THEN** the object name ends with `.jpg`

#### Scenario: MIME type mapped to extension for PNG
- **WHEN** an image with MIME type `image/png` is uploaded
- **THEN** the object name ends with `.png`

#### Scenario: Unknown MIME type uses bin extension
- **WHEN** an image with an unrecognized MIME type is uploaded
- **THEN** the object name ends with `.bin`

### Requirement: GCS bucket configurable via environment variable
The GCS bucket name SHALL be configurable via the `GCS_BUCKET_NAME` environment variable, defaulting to `master-agent-images` if not set.

#### Scenario: Custom bucket name used when env var set
- **WHEN** `GCS_BUCKET_NAME=my-custom-bucket` is set
- **THEN** all uploads go to `gs://my-custom-bucket/`

#### Scenario: Default bucket used when env var absent
- **WHEN** `GCS_BUCKET_NAME` is not set
- **THEN** uploads go to `gs://master-agent-images/`
