## 1. Models

- [x] 1.1 Добавить модель `ImageRequest` в `agent/models.py`
- [x] 1.2 Добавить модель `ImageResponse` в `agent/models.py`

## 2. MediaClient

- [x] 2.1 Переименовать `voice_client.py` → `media_client.py`
- [x] 2.2 Переименовать класс `VoiceClient` → `MediaClient`
- [x] 2.3 Добавить метод `describe_image()` в `MediaClient`
- [x] 2.4 Обновить импорты в `app.py`

## 3. Processor

- [x] 3.1 Добавить метод `process_image()` в `MessageProcessor`
- [x] 3.2 Обновить импорты в `processor.py`

## 4. API Endpoint

- [x] 4.1 Добавить endpoint `POST /api/image` в `app.py`
- [x] 4.2 Добавить обработку ошибок (invalid base64, unsupported mime_type)

## 5. Testing

- [x] 5.1 Протестировать endpoint с изображением без prompt
- [x] 5.2 Протестировать endpoint с изображением и prompt
- [x] 5.3 Протестировать сохранение контекста сессии (image → text follow-up)

## 6. Documentation

- [x] 6.1 Обновить `docs/telegram-bot-integration.md` с описанием image endpoint
- [x] 6.2 Обновить `README.md` с новым endpoint

## 7. Deploy

- [x] 7.1 Задеплоить обновлённый master-agent
- [x] 7.2 Проверить endpoint в production
