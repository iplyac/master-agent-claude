## Context

Текущий агент использует прямые HTTP-вызовы к Gemini API через `httpx` и самописное хранение истории разговоров в Firestore. Это работает, но:
- Нет стандартизированной архитектуры для добавления tools
- Ручное управление историей и сессиями
- Дублирование логики, которую ADK предоставляет "из коробки"

ADK (google-adk v1.23.0) предлагает:
- `Agent` — декларативное определение агента с моделью и инструкциями
- `Runner` — оркестратор для выполнения агента
- `SessionService` — абстракция хранения сессий с готовыми реализациями

## Goals / Non-Goals

**Goals:**
- Заменить LLMClient на ADK Agent с сохранением всей функциональности
- Использовать ADK SessionService для персистентности разговоров (Firestore backend)
- Telegram conversation_id должен мапиться на ADK session_id для сохранения контекста
- Сохранить текущий FastAPI API контракт без изменений

**Non-Goals:**
- Добавление новых tools (агент остаётся conversational)
- Использование ADK CLI (`adk web`, `adk run`) — интеграция только программная
- Миграция на Vertex AI Agent Engine — используем standalone ADK
- Изменение формата хранения в Firestore (если ADK использует другой формат — это ОК)

## Decisions

### 1. SessionService: DatabaseSessionService vs Custom Firestore

**Решение:** Использовать `DatabaseSessionService` с SQLite/PostgreSQL ИЛИ реализовать custom `FirestoreSessionService`.

**Альтернативы:**
- `InMemorySessionService` — не подходит, теряет данные при рестарте
- `VertexAiSessionService` — требует Vertex AI Agent Engine, избыточно
- `DatabaseSessionService` — поддерживает PostgreSQL/SQLite, но не Firestore напрямую

**Выбор:** Реализовать **custom FirestoreSessionService**, наследуя от базового интерфейса. Это сохранит существующую инфраструктуру Firestore и обеспечит персистентность.

Структура:
```python
class FirestoreSessionService(BaseSessionService):
    async def create_session(app_name, user_id, session_id) -> Session
    async def get_session(app_name, user_id, session_id) -> Session | None
    async def list_sessions(app_name, user_id) -> list[Session]
    async def delete_session(app_name, user_id, session_id) -> None
```

### 2. Session ID mapping

**Решение:** Использовать `conversation_id` из Telegram напрямую как `session_id` в ADK.

**Логика:**
- `app_name` = "master-agent" (константа)
- `user_id` = conversation_id (например, "tg_123456789")
- `session_id` = conversation_id (тот же, для простоты)

Это обеспечит: один чат Telegram = одна сессия ADK = сохранение контекста.

### 3. Runner integration с FastAPI

**Решение:** Создать `Runner` в lifespan и хранить в `app.state`.

```python
@asynccontextmanager
async def lifespan(app: FastAPI):
    agent = Agent(
        name="master-agent",
        model="gemini-2.0-flash",
        instruction="...",
    )
    session_service = FirestoreSessionService(project_id)
    runner = Runner(
        agent=agent,
        app_name="master-agent",
        session_service=session_service,
    )
    app.state.runner = runner
    yield
```

### 4. Обработка ответов: Event stream

**Решение:** Использовать `runner.run_async()` и ждать `event.is_final_response()`.

```python
async def process_message(runner, session_id, message):
    content = types.Content(role='user', parts=[types.Part(text=message)])
    async for event in runner.run_async(
        user_id=session_id,
        session_id=session_id,
        new_message=content,
    ):
        if event.is_final_response():
            return event.content.parts[0].text
```

### 5. Voice messages

**Решение:** Временно сохранить прямой вызов Gemini API для голосовых сообщений.

ADK не имеет встроенной поддержки multimodal audio input в `run_async`. Варианты:
- Создать custom tool для audio processing
- Оставить отдельный LLM-вызов для voice

**Выбор:** Оставить `generate_response_from_audio` как отдельный метод, вне ADK Runner. Это минимизирует изменения и сохраняет функциональность. В будущем можно мигрировать на ADK tools.

## Risks / Trade-offs

| Risk | Mitigation |
|------|------------|
| ADK API может измениться (v1.x) | Зафиксировать версию в requirements.txt, следить за changelog |
| Custom FirestoreSessionService требует реализации | Интерфейс простой (~5 методов), Firestore SDK уже используется |
| Voice остаётся вне ADK | Документировать как tech debt, запланировать миграцию |
| Формат истории в Firestore изменится | Это ОК — ADK использует свой формат Event, старые данные не нужны |
| Увеличение latency из-за абстракций ADK | Мониторить в Cloud Trace, оптимизировать при необходимости |

## Migration Plan

1. **Добавить зависимость** `google-adk` в requirements.txt
2. **Создать FirestoreSessionService** в `agent/adk_session_service.py`
3. **Создать ADK Agent** в `agent/adk_agent.py`
4. **Обновить processor.py** для использования Runner
5. **Обновить app.py** — lifespan с ADK компонентами
6. **Удалить** `llm_client.py` (кроме voice методов)
7. **Обновить тесты**
8. **Удалить** `google-generativeai` из requirements.txt

**Rollback:** Git revert + redeploy предыдущей версии.

## Open Questions

- [ ] Нужна ли миграция существующей истории разговоров из старого формата?
- [ ] Какой формат использует ADK для хранения Events в session? (влияет на структуру Firestore документов)
