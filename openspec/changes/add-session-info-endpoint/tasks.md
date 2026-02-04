## 1. Implement Session Info Endpoint

- [x] 1.1 Добавить модель `SessionInfoRequest` в `agent/models.py`
- [x] 1.2 Добавить модель `SessionInfoResponse` в `agent/models.py`
- [x] 1.3 Добавить endpoint `POST /api/session-info` в `app.py`
- [x] 1.4 Реализовать логику проверки существования сессии через session_service

## 2. Testing

- [x] 2.1 Протестировать endpoint с существующей сессией
- [x] 2.2 Протестировать endpoint с несуществующей сессией
- [x] 2.3 Протестировать endpoint без conversation_id (ожидается 400)

## 3. Documentation

- [x] 3.1 Создать файл `docs/telegram-bot-integration.md` с инструкцией
- [x] 3.2 Описать формат запроса/ответа endpoint
- [x] 3.3 Добавить пример кода для команды `/sessioninfo` в telegram-bot

## 4. Deploy

- [x] 4.1 Задеплоить обновлённый master-agent
- [x] 4.2 Проверить endpoint в production
