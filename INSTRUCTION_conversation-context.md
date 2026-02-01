# Инструкция: Обновление API для Conversation Context

## Контекст

Telegram-bot переходит на новый формат запросов с `conversation_id` вместо `session_id`.
Master-agent должен поддержать новый формат с обратной совместимостью.

## Новый формат запроса

### POST /api/chat

**Новый формат (приоритет):**
```json
{
  "conversation_id": "tg_dm_123456",
  "message": "Привет!",
  "metadata": {
    "telegram": {
      "chat_id": 123456,
      "user_id": 789012,
      "chat_type": "private"
    }
  }
}
```

**Старый формат (deprecated, для обратной совместимости):**
```json
{
  "session_id": "tg_123456",
  "message": "Привет!"
}
```

### POST /api/voice

**Новый формат:**
```json
{
  "conversation_id": "tg_dm_123456",
  "audio_base64": "<base64>",
  "mime_type": "audio/ogg",
  "metadata": {
    "telegram": {
      "chat_id": 123456,
      "user_id": 789012,
      "chat_type": "private"
    }
  }
}
```

## Задачи

### 1. Обновить модель запроса

Добавить поддержку обоих форматов:

```python
from typing import Optional
from pydantic import BaseModel

class TelegramMetadata(BaseModel):
    chat_id: int
    user_id: int
    chat_type: str  # "private", "group", "supergroup"

class RequestMetadata(BaseModel):
    telegram: Optional[TelegramMetadata] = None

class ChatRequest(BaseModel):
    # Новый формат
    conversation_id: Optional[str] = None
    message: str
    metadata: Optional[RequestMetadata] = None

    # Старый формат (deprecated)
    session_id: Optional[str] = None

    def get_conversation_id(self) -> str:
        """Return conversation_id, falling back to session_id for backward compatibility."""
        if self.conversation_id:
            return self.conversation_id
        if self.session_id:
            # Log deprecation warning
            return self.session_id
        raise ValueError("Either conversation_id or session_id is required")
```

### 2. Обновить endpoint /api/chat

```python
@app.post("/api/chat")
async def chat(request: ChatRequest):
    conversation_id = request.get_conversation_id()

    # Log deprecation if using old format
    if request.session_id and not request.conversation_id:
        logger.warning(
            "Deprecated session_id format used",
            extra={"session_id": request.session_id}
        )

    # Use conversation_id for session management
    response = await process_message(conversation_id, request.message)

    return {"response": response}
```

### 3. Обновить endpoint /api/voice

Аналогично `/api/chat`.

### 4. Использование metadata

Metadata может быть полезна для:
- Различия поведения в группах vs DM
- Логирования для отладки
- Будущих фич (упоминания, reply, и т.д.)

```python
if request.metadata and request.metadata.telegram:
    tg = request.metadata.telegram
    logger.info(
        "Processing message",
        extra={
            "conversation_id": conversation_id,
            "chat_type": tg.chat_type,
            "chat_id": tg.chat_id,
            "user_id": tg.user_id,
        }
    )
```

## Формат conversation_id

| Chat Type | Format | Example |
|-----------|--------|---------|
| Private (DM) | `tg_dm_{user_id}` | `tg_dm_123456` |
| Group | `tg_group_{chat_id}` | `tg_group_-100123456` |
| Supergroup | `tg_group_{chat_id}` | `tg_group_-100789012` |
| Unknown | `tg_chat_{chat_id}` | `tg_chat_-100111222` |

## Тестирование

```bash
# Новый формат
curl -X POST http://localhost:8080/api/chat \
  -H "Content-Type: application/json" \
  -d '{
    "conversation_id": "tg_dm_123456",
    "message": "test",
    "metadata": {
      "telegram": {
        "chat_id": 123456,
        "user_id": 123456,
        "chat_type": "private"
      }
    }
  }'

# Старый формат (должен работать с warning в логах)
curl -X POST http://localhost:8080/api/chat \
  -H "Content-Type: application/json" \
  -d '{
    "session_id": "tg_123456",
    "message": "test"
  }'
```

## Чеклист

- [ ] Обновить ChatRequest model с новыми полями
- [ ] Добавить TelegramMetadata и RequestMetadata models
- [ ] Обновить /api/chat endpoint
- [ ] Обновить /api/voice endpoint
- [ ] Добавить логирование deprecation warning
- [ ] Добавить логирование metadata
- [ ] Протестировать новый формат
- [ ] Протестировать обратную совместимость
