## MODIFIED Requirements

### Requirement: Processing summary message is formatted
After a successful document processing response, the system SHALL send a formatted text message to the user that includes: the original filename, the number of pages (if available), the number of tables found (if available), the number of images found (if available), the processing time in seconds (if available), and the AI-generated document description (if present in the response). Fields not present in the metadata or response SHALL be omitted from the summary.

#### Scenario: Full metadata and summary available
- **WHEN** master-agent returns full metadata and a non-empty `summary`
- **THEN** the bot sends a message that includes stats (pages, tables, images, time) followed by the summary text

#### Scenario: Summary absent
- **WHEN** master-agent returns metadata but `summary` is null or absent
- **THEN** the bot sends the stats message without a summary section (behaviour unchanged from before)

#### Scenario: Partial metadata available
- **WHEN** master-agent returns metadata with only pages=5 and no tables_found or images_found
- **THEN** the bot sends a summary showing pages only, omitting missing fields

#### Scenario: No metadata returned
- **WHEN** master-agent returns no metadata
- **THEN** the bot sends a minimal summary with only the filename
