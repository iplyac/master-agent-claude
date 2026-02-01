## 1. Dependencies

- [x] 1.1 Добавить `google-cloud-firestore` в `requirements.txt`
- [x] 1.2 Проверить что Cloud Run SA имеет роль `roles/datastore.user`

## 2. Pydantic Models

- [x] 2.1 Создать `TelegramMetadata` model (chat_id, user_id, chat_type)
- [x] 2.2 Создать `RequestMetadata` model (telegram: Optional[TelegramMetadata])
- [x] 2.3 Обновить `ChatRequest` model — добавить conversation_id и metadata
- [x] 2.4 Добавить метод `get_conversation_id()` с fallback на session_id
- [x] 2.5 Создать/обновить `VoiceRequest` model аналогично ChatRequest

## 3. ConversationStore

- [x] 3.1 Создать файл `conversation_store.py`
- [x] 3.2 Реализовать класс `ConversationMapping` (providers dict, metadata, timestamps)
- [x] 3.3 Реализовать класс `ConversationStore` с Firestore client
- [x] 3.4 Реализовать метод `get(conversation_id)` — загрузка из Firestore
- [x] 3.5 Реализовать метод `save(conversation_id, mapping)` — сохранение в Firestore
- [x] 3.6 Реализовать метод `get_or_create_provider_session(conversation_id, provider)`
- [x] 3.7 Добавить error handling для Firestore unavailable (503)

## 4. API Endpoints

- [x] 4.1 Обновить `/api/chat` — использовать `request.get_conversation_id()`
- [x] 4.2 Добавить deprecation warning при использовании session_id
- [x] 4.3 Добавить логирование metadata.telegram если присутствует
- [x] 4.4 Обновить `/api/voice` аналогично /api/chat
- [x] 4.5 Добавить validation error 400 если нет ни conversation_id ни session_id

## 5. Integration

- [x] 5.1 Инициализировать ConversationStore в app.py
- [x] 5.2 Интегрировать ConversationStore с agent logic (получение provider session)
- [x] 5.3 Сохранять mapping после создания нового provider session

## 6. Testing

- [x] 6.1 Тест: новый формат с conversation_id
- [x] 6.2 Тест: старый формат с session_id (backward compat)
- [x] 6.3 Тест: ошибка если нет ни conversation_id ни session_id
- [x] 6.4 Тест: conversation mapping persistence

## 7. Deployment

- [ ] 7.1 Деплой и проверка health check
- [ ] 7.2 Тест с telegram-bot (новый формат)
- [ ] 7.3 Тест с telegram-bot (старый формат для backward compat)
