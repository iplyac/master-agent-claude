## Context

Master-agent использует `InMemorySessionService` — сессии живут только в памяти контейнера и теряются при рестарте. Агент не помнит пользователей между деплоями. Vertex AI предоставляет два связанных сервиса:

1. **VertexAiSessionService** — сохраняет историю разговоров (events) в Vertex AI Agent Engine, заменяя InMemorySessionService
2. **VertexAiMemoryBankService** — извлекает ключевые факты из разговоров и хранит их как долгосрочную память по user_id

Оба сервиса уже интегрированы в ADK SDK (`google.adk.sessions.VertexAiSessionService`, `google.adk.memory.VertexAiMemoryBankService`).

## Goals / Non-Goals

**Goals:**
- Заменить InMemorySessionService на VertexAiSessionService для персистентных сессий
- Добавить VertexAiMemoryBankService для долгосрочной памяти
- Добавить PreloadMemoryTool к агенту для автоматической подгрузки воспоминаний
- Сохранять сессии в долгосрочную память после обработки сообщений
- Сделать Memory Bank опциональным через env var (fallback на InMemory)

**Non-Goals:**
- Миграция существующих in-memory сессий (они одноразовые)
- Ручное управление воспоминаниями через API (CRUD)
- UI для просмотра или редактирования памяти
- Создание Agent Engine через код (используем существующий или создаём вручную)

## Decisions

### 1. Опциональность через AGENT_ENGINE_ID

**Decision**: Если `AGENT_ENGINE_ID` env var установлен — используем VertexAiSessionService + VertexAiMemoryBankService. Если нет — fallback на InMemorySessionService без памяти.

**Rationale**: Позволяет запускать локально и в тестах без Agent Engine. Agent Engine создаётся вручную в GCP Console или через gcloud, не в коде приложения.

**Alternative considered**: Автоматическое создание Agent Engine при запуске — отклонено, т.к. это одноразовое действие, которое лучше делать вручную (идемпотентность, контроль ресурсов).

### 2. PreloadMemoryTool вместо ручного search_memory

**Decision**: Добавить `PreloadMemoryTool` в tools агента. Это автоматически подгружает релевантные воспоминания в начале каждого хода.

**Rationale**: Не требует изменений в processor.py — ADK Runner сам вызывает tool. Проще и надёжнее чем ручной search_memory.

**Alternative considered**: Ручной вызов `search_memory` в `process()` перед отправкой сообщения — отклонено, усложняет процессор и дублирует функциональность встроенного tool.

### 3. add_session_to_memory после каждого сообщения

**Decision**: Вызывать `memory_service.add_session_to_memory(session)` после каждого завершённого хода агента в `process()`.

**Rationale**: Memory Bank сам решает какие факты извлекать и хранить — мы просто передаём сессию. Частые вызовы не проблема — сервис дедуплицирует факты.

**Alternative considered**: Вызывать только при "завершении разговора" — отклонено, т.к. нет надёжного сигнала завершения в Telegram (пользователь просто перестаёт писать).

### 4. Конфигурация memory_service в processor

**Decision**: Передать `memory_service` как опциональный параметр в `MessageProcessor.__init__()`. Если `None` — не вызываем `add_session_to_memory`.

**Rationale**: Следует существующему паттерну `media_client` — опциональная зависимость, graceful fallback.

### 5. Использование conversation_id как user_id

**Decision**: Продолжаем использовать `conversation_id` (формат `tg_dm_{chat_id}`) как `user_id` для ADK — воспоминания привязаны к конкретному чату.

**Rationale**: В Telegram приватный чат = один пользователь. Для групповых чатов (`tg_group_{chat_id}`) — общая память группы, что тоже логично.

## Risks / Trade-offs

- **[Latency increase]** → VertexAiSessionService делает сетевые вызовы вместо in-memory. Mitigation: Vertex AI Agent Engine развёрнут в том же регионе (europe-west4).
- **[Memory Bank availability]** → Memory Bank в public preview. Mitigation: AGENT_ENGINE_ID опционален, fallback на InMemory.
- **[Cost]** → Каждый вызов add_session_to_memory использует LLM для извлечения фактов. Mitigation: Стоимость минимальна при небольшом объёме сообщений.
- **[Region support]** → Memory Bank может быть недоступен в europe-west4. Mitigation: Проверить доступность, при необходимости использовать us-central1 для Agent Engine.
