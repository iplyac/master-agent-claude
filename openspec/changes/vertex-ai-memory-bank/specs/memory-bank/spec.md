## ADDED Requirements

### Requirement: Long-term memory via Vertex AI Memory Bank
Сервис SHALL сохранять долгосрочную память разговоров через Vertex AI Memory Bank, привязанную к user_id.

#### Scenario: Memory extraction after message processing
- **WHEN** агент завершает обработку сообщения пользователя
- **THEN** текущая сессия передаётся в `memory_service.add_session_to_memory()` для извлечения и сохранения фактов

#### Scenario: Memory retrieval at conversation start
- **WHEN** пользователь отправляет сообщение
- **THEN** агент автоматически подгружает релевантные воспоминания через `PreloadMemoryTool`

#### Scenario: Memory scoping by user
- **WHEN** воспоминания сохраняются
- **THEN** они привязаны к `user_id` (conversation_id) и `app_name`

#### Scenario: Memory Bank not configured
- **WHEN** `AGENT_ENGINE_ID` не установлен
- **THEN** сервис работает без долгосрочной памяти (graceful fallback)

### Requirement: Agent Engine configuration
Сервис SHALL принимать ID существующего Agent Engine через переменную окружения.

#### Scenario: Agent Engine ID from env var
- **WHEN** переменная `AGENT_ENGINE_ID` установлена
- **THEN** сервис подключается к указанному Agent Engine для сессий и памяти

#### Scenario: Agent Engine ID not set
- **WHEN** переменная `AGENT_ENGINE_ID` не установлена
- **THEN** сервис использует `InMemorySessionService` без Memory Bank

### Requirement: PreloadMemoryTool in agent
Агент SHALL использовать `PreloadMemoryTool` для автоматической подгрузки воспоминаний.

#### Scenario: Tool added to agent
- **WHEN** Memory Bank сконфигурирован (AGENT_ENGINE_ID установлен)
- **THEN** агент создаётся с `PreloadMemoryTool` в списке tools

#### Scenario: Tool not added without Memory Bank
- **WHEN** Memory Bank не сконфигурирован
- **THEN** агент создаётся без `PreloadMemoryTool`
