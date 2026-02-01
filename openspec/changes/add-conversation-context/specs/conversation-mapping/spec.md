## ADDED Requirements

### Requirement: Conversation ID as primary key

Система SHALL использовать `conversation_id` как primary key для идентификации диалогов.

#### Scenario: Unique conversation identification
- **WHEN** приходит запрос с `conversation_id`
- **THEN** система использует его для lookup/create conversation mapping

### Requirement: Provider session mapping

Система SHALL поддерживать маппинг одного `conversation_id` на несколько LLM provider sessions.

#### Scenario: Multiple providers per conversation
- **WHEN** conversation существует с Gemini session
- **THEN** система может создать отдельный OpenAI session для того же conversation_id

#### Scenario: Provider session isolation
- **WHEN** один provider session сбрасывается
- **THEN** другие provider sessions остаются неизменными

### Requirement: Persistent storage in Firestore

Система SHALL хранить conversation mappings в Firestore.

#### Scenario: Mapping persisted
- **WHEN** создается новый provider session
- **THEN** mapping сохраняется в Firestore collection `conversations`

#### Scenario: Mapping retrieved
- **WHEN** приходит запрос с существующим conversation_id
- **THEN** система загружает mapping из Firestore

### Requirement: Auto-create on missing mapping

Система SHALL автоматически создавать новый mapping если он не существует.

#### Scenario: New conversation
- **WHEN** приходит запрос с неизвестным conversation_id
- **THEN** создается новый mapping с пустым списком provider sessions

### Requirement: Get or create provider session

Система SHALL предоставлять метод для получения или создания provider-specific session.

#### Scenario: Existing provider session
- **WHEN** запрашивается session для provider у которого уже есть session
- **THEN** возвращается существующий session_id

#### Scenario: New provider session
- **WHEN** запрашивается session для нового provider
- **THEN** создается новый session_id и сохраняется в mapping

### Requirement: Stateless master-agent instances

Система SHALL быть stateless — все состояние хранится в Firestore.

#### Scenario: Instance restart
- **WHEN** master-agent instance перезапускается
- **THEN** conversation mappings доступны из Firestore

### Requirement: Graceful storage failure handling

Система SHALL корректно обрабатывать недоступность Firestore.

#### Scenario: Storage unavailable
- **WHEN** Firestore недоступен
- **THEN** запрос завершается с ошибкой 503 Service Unavailable
