## ADDED Requirements

### Requirement: Image recognition endpoint

Сервис SHALL предоставлять endpoint `POST /api/image` для приёма и обработки изображений.

#### Scenario: Describe image without prompt
- **WHEN** POST запрос на `/api/image` с `image_base64` и без `prompt`
- **THEN** возвращается описание содержимого изображения в поле `response`

#### Scenario: Answer question about image
- **WHEN** POST запрос на `/api/image` с `image_base64` и `prompt` (вопрос)
- **THEN** возвращается ответ на вопрос о содержимом изображения

#### Scenario: Missing image
- **WHEN** POST запрос на `/api/image` без `image_base64`
- **THEN** возвращается HTTP 400 с ошибкой

#### Scenario: Invalid image format
- **WHEN** POST запрос на `/api/image` с некорректным base64 или неподдерживаемым mime_type
- **THEN** возвращается HTTP 400 с описанием ошибки

### Requirement: Request format

Запрос SHALL содержать стандартизированный JSON формат.

#### Scenario: Full request structure
- **WHEN** запрос содержит все поля
- **THEN** принимаются поля: `conversation_id`, `image_base64`, `mime_type`, `prompt` (optional), `metadata` (optional)

#### Scenario: Supported mime types
- **WHEN** `mime_type` указан
- **THEN** поддерживаются: `image/jpeg`, `image/png`, `image/webp`, `image/gif`

### Requirement: Response format

Ответ endpoint SHALL содержать стандартизированный JSON формат.

#### Scenario: Success response structure
- **WHEN** запрос успешен
- **THEN** ответ содержит поля: `response` (текст ответа), `description` (описание изображения)

### Requirement: Session context preservation

Обработка изображений SHALL сохранять контекст сессии.

#### Scenario: Image in conversation history
- **WHEN** пользователь отправляет изображение
- **AND** затем отправляет текстовое сообщение "а что ещё на картинке?"
- **THEN** агент помнит содержимое предыдущего изображения и отвечает в контексте
