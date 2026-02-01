## ADDED Requirements

### Requirement: FirestoreSessionService implementation
The system SHALL implement a custom SessionService that persists sessions to Google Cloud Firestore.

#### Scenario: Service initialization
- **WHEN** FirestoreSessionService is instantiated with project_id
- **THEN** Firestore client is created
- **AND** service is ready to manage sessions

### Requirement: Session creation
The system SHALL create new sessions in Firestore when a new conversation starts.

#### Scenario: New session created
- **WHEN** create_session is called with app_name, user_id, and session_id
- **THEN** new document is created in Firestore "adk_sessions" collection
- **AND** document contains session metadata (id, app_name, user_id, created_at)
- **AND** document contains empty events list
- **AND** Session object is returned

#### Scenario: Session already exists
- **WHEN** create_session is called with existing session_id
- **THEN** existing session is returned without modification

### Requirement: Session retrieval
The system SHALL retrieve existing sessions from Firestore.

#### Scenario: Session exists
- **WHEN** get_session is called with valid session_id
- **THEN** Session object is returned with all stored events

#### Scenario: Session not found
- **WHEN** get_session is called with non-existent session_id
- **THEN** None is returned

### Requirement: Event persistence
The system SHALL persist conversation events to Firestore after each interaction.

#### Scenario: Events appended after agent response
- **WHEN** runner.run_async() completes and yields non-partial events
- **THEN** events are automatically saved to session document in Firestore
- **AND** events include user message and agent response

#### Scenario: Events retrieved on session load
- **WHEN** session is retrieved from Firestore
- **THEN** all previously stored events are loaded into Session.events

### Requirement: Session ID mapping from Telegram
The system SHALL use Telegram conversation_id as ADK session identifier.

#### Scenario: Telegram chat maps to session
- **WHEN** message arrives with conversation_id "tg_123456789"
- **THEN** session_id used in ADK is "tg_123456789"
- **AND** user_id used in ADK is "tg_123456789"
- **AND** app_name is "master-agent"

### Requirement: Session listing
The system SHALL support listing sessions for a user.

#### Scenario: List user sessions
- **WHEN** list_sessions is called with app_name and user_id
- **THEN** list of Session objects for that user is returned

### Requirement: Session deletion
The system SHALL support deleting sessions.

#### Scenario: Delete existing session
- **WHEN** delete_session is called with valid session_id
- **THEN** session document is removed from Firestore

#### Scenario: Delete non-existent session
- **WHEN** delete_session is called with non-existent session_id
- **THEN** operation completes without error

### Requirement: History size limit
The system SHALL limit the number of events stored per session to prevent unbounded growth.

#### Scenario: Events exceed limit
- **WHEN** session has more than 100 events
- **THEN** oldest events are removed to maintain limit of 100
- **AND** most recent events are preserved
