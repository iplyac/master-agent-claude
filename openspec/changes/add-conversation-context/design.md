## Context

Master-agent сейчас использует `session_id` для идентификации сессий, но:
- Не сохраняет контекст между запросами
- Не поддерживает маппинг на разные LLM провайдеры
- Telegram-bot переходит на новый формат с `conversation_id`

Референсы:
- `/Users/iosifplyats/Documents/master-agent-conversation-spec.md`
- `INSTRUCTION_conversation-context.md`

## Goals / Non-Goals

**Goals:**
- Поддержка нового формата API с `conversation_id` и `metadata`
- Обратная совместимость со старым `session_id` форматом
- Персистентное хранение conversation mappings в Firestore
- Маппинг conversation_id → LLM provider session IDs

**Non-Goals:**
- Cross-provider context merging (future)
- Unified memory replay (future)
- Long-term summarization (future)

## Decisions

### 1. Firestore как хранилище

**Решение:** Использовать Firestore для хранения conversation mappings.

**Альтернативы:**
- Redis → требует отдельной инфраструктуры
- In-memory → теряется при рестарте
- Cloud SQL → избыточно для key-value

**Структура документа:**
```
conversations/{conversation_id}
├── providers
│   ├── gemini: {session_id: "..."}
│   ├── openai: {session_id: "..."}
│   └── ...
├── metadata
│   └── telegram: {chat_id, user_id, chat_type}
├── created_at
└── updated_at
```

### 2. API модели с Pydantic

**Решение:** Использовать Pydantic models для валидации:

```python
class TelegramMetadata(BaseModel):
    chat_id: int
    user_id: int
    chat_type: str

class RequestMetadata(BaseModel):
    telegram: Optional[TelegramMetadata] = None

class ChatRequest(BaseModel):
    conversation_id: Optional[str] = None
    message: str
    metadata: Optional[RequestMetadata] = None
    session_id: Optional[str] = None  # deprecated
```

### 3. Backward compatibility через fallback

**Решение:** `get_conversation_id()` метод с fallback на `session_id`:

```python
def get_conversation_id(self) -> str:
    if self.conversation_id:
        return self.conversation_id
    if self.session_id:
        logger.warning("Deprecated session_id format")
        return self.session_id
    raise ValueError("conversation_id or session_id required")
```

### 4. Формат conversation_id

**Решение:** Telegram-bot определяет формат:

| Chat Type | Format |
|-----------|--------|
| Private | `tg_dm_{user_id}` |
| Group | `tg_group_{chat_id}` |
| Supergroup | `tg_group_{chat_id}` |

### 5. ConversationStore abstraction

**Решение:** Отдельный модуль `conversation_store.py`:

```python
class ConversationStore:
    async def get(self, conversation_id: str) -> Optional[ConversationMapping]
    async def save(self, conversation_id: str, mapping: ConversationMapping)
    async def get_or_create_provider_session(
        self, conversation_id: str, provider: str
    ) -> str
```

## Risks / Trade-offs

**[Risk] Firestore latency**
→ Mitigation: Async calls, caching if needed

**[Risk] Missing Firestore permissions**
→ Mitigation: Cloud Run SA needs `roles/datastore.user`

**[Trade-off] Separate storage for each provider session**
→ Intentional for provider isolation and future flexibility
