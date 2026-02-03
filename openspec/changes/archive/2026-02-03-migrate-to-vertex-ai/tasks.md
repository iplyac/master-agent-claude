## 1. IAM Configuration

- [x] 1.1 Добавить роль `Vertex AI User` к service account Cloud Run
- [x] 1.2 Проверить что Vertex AI API включен в проекте

## 2. Code Changes

- [x] 2.1 Обновить `agent/config.py`: добавить функцию `get_location()` для GCP_LOCATION
- [x] 2.2 Обновить `app.py`: заменить `FirestoreSessionService` на `VertexAiSessionService`
- [x] 2.3 Обновить `app.py`: убрать зависимость от `get_model_api_key()` для основного flow
- [x] 2.4 Удалить файл `agent/adk_session_service.py`
- [x] 2.5 Обновить импорты в `app.py`: убрать FirestoreSessionService, добавить VertexAiSessionService

## 3. Voice Client (Optional)

- [x] 3.1 Решить: оставить voice на API key или временно отключить
- [x] 3.2 Мигрировать voice на Vertex AI (вместо сохранения API key)

## 4. Deployment Configuration

- [x] 4.1 Обновить команду деплоя: убрать `--set-secrets="GOOGLE_API_KEY=..."`
- [x] 4.2 Добавить/проверить env vars: GCP_PROJECT_ID, GCP_LOCATION=europe-west4
- [x] 4.3 Задеплоить новую версию на Cloud Run

## 5. Testing

- [x] 5.1 Проверить health endpoint после деплоя
- [x] 5.2 Отправить тестовое сообщение через /api/chat
- [x] 5.3 Отправить второе сообщение — убедиться что нет 429 ошибки
- [x] 5.4 Проверить сохранение контекста между сообщениями

## 6. Cleanup

- [x] 6.1 Удалить секрет GOOGLE_API_KEY из Secret Manager — SKIPPED (оставлен как fallback)
- [x] 6.2 Удалить неиспользуемый код связанный с Firestore session (adk_session_service.py удалён)
