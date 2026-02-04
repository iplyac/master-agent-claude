## Why

Telegram-bot получает от пользователей изображения (фото), но master-agent не умеет их обрабатывать. Нужно добавить endpoint для приёма изображений в base64 и распознавания их содержимого через Gemini multimodal API.

## What Changes

- Добавить новый endpoint `POST /api/image` для приёма изображений
- Добавить модели `ImageRequest` и `ImageResponse` в `agent/models.py`
- Расширить `VoiceClient` или создать `ImageClient` для обработки изображений через Vertex AI
- Интегрировать обработку изображений с ADK Runner для сохранения контекста сессии

## Capabilities

### New Capabilities
- `image-recognition-api`: API endpoint для приёма и распознавания изображений через Gemini multimodal

### Modified Capabilities
- `vertex-ai-backend`: Добавление поддержки image content type в multimodal запросах

## Impact

- **API**: Новый endpoint `/api/image`
- **Models**: Новые Pydantic модели для image request/response
- **Dependencies**: Использует существующий google-genai SDK (уже поддерживает images)
- **Telegram-bot**: Потребуется интеграция для отправки фото через новый endpoint
