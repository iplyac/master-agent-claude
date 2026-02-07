## 1. Endpoint

- [x] 1.1 Добавить эндпоинт `POST /api/reload-prompt` в `app.py`
- [x] 1.2 Реализовать загрузку промпта и пересоздание агента
- [x] 1.3 Добавить обработку ошибок (prompt ID not configured, Vertex AI error)

## 2. Agent Management

- [x] 2.1 Добавить asyncio.Lock для сериализации reload операций
- [x] 2.2 Обновить `app.state.runner` с новым агентом
- [x] 2.3 Сохранять session_service при reload

## 3. Testing

- [x] 3.1 Протестировать успешный reload локально
- [x] 3.2 Протестировать ошибку при отсутствии AGENT_PROMPT_ID

## 4. Deploy

- [x] 4.1 Задеплоить обновлённый master-agent
- [x] 4.2 Проверить reload через curl/Telegram бот
