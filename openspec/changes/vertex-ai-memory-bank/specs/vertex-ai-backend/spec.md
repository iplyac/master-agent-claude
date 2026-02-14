## MODIFIED Requirements

### Requirement: InMemorySessionService для хранения сессий

Сервис SHALL использовать `VertexAiSessionService` из ADK для управления сессиями при наличии `AGENT_ENGINE_ID`, с fallback на `InMemorySessionService`.

#### Scenario: Создание сессии
- **WHEN** поступает первое сообщение от нового conversation_id
- **AND** `AGENT_ENGINE_ID` установлен
- **THEN** VertexAiSessionService создаёт новую сессию в Vertex AI Agent Engine

#### Scenario: Восстановление истории в рамках сессии
- **WHEN** поступает сообщение от существующего conversation_id
- **AND** `AGENT_ENGINE_ID` установлен
- **THEN** VertexAiSessionService загружает историю событий из Vertex AI Agent Engine

#### Scenario: Fallback на InMemorySessionService
- **WHEN** `AGENT_ENGINE_ID` не установлен
- **THEN** используется InMemorySessionService (существующее поведение)
