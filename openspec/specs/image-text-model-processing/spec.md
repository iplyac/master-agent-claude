## ADDED Requirements

### Requirement: Image processing with Nano Banana Pro model
The system SHALL process image+prompt requests through the Nano Banana Pro model (`gemini-3-pro-image-preview` by default) and return both a text response and a processed image.

#### Scenario: Image with text prompt processed by model
- **WHEN** POST запрос на `/api/image` с `image_base64` и `prompt`
- **THEN** изображение и промпт отправляются в модель Nano Banana Pro
- **AND** возвращается текстовый ответ в поле `response`
- **AND** возвращается обработанное изображение в поле `processed_image_base64`
- **AND** возвращается MIME тип обработанного изображения в поле `processed_image_mime_type`

#### Scenario: Image without prompt uses existing description flow
- **WHEN** POST запрос на `/api/image` с `image_base64` без `prompt`
- **THEN** обработка идёт через существующий pipeline описания изображения (Gemini)
- **AND** поля `processed_image_base64` и `processed_image_mime_type` возвращаются как `null`

#### Scenario: Model returns only text without processed image
- **WHEN** модель Nano Banana Pro возвращает только текст без изображения
- **THEN** `processed_image_base64` и `processed_image_mime_type` возвращаются как `null`
- **AND** текстовый ответ возвращается в поле `response`

#### Scenario: Model processing error
- **WHEN** вызов модели Nano Banana Pro завершается ошибкой
- **THEN** возвращается HTTP 500 с сообщением об ошибке

### Requirement: Image model configuration
The system SHALL allow configuring the image processing model via the `IMAGE_MODEL_NAME` environment variable.

#### Scenario: Custom model name configured
- **WHEN** переменная окружения `IMAGE_MODEL_NAME` установлена
- **THEN** система использует указанную модель для обработки изображений с промптом

#### Scenario: Default model name
- **WHEN** переменная окружения `IMAGE_MODEL_NAME` не установлена
- **THEN** система использует `gemini-3-pro-image-preview` по умолчанию

### Requirement: Extended response format
The `/api/image` endpoint response SHALL include optional fields for the processed image.

#### Scenario: Response with processed image
- **WHEN** запрос обработан через Nano Banana Pro и модель вернула изображение
- **THEN** ответ содержит: `response` (текст), `description` (текст от модели), `processed_image_base64` (base64 изображения), `processed_image_mime_type` (MIME тип)

#### Scenario: Response without processed image
- **WHEN** запрос обработан без модели или модель не вернула изображение
- **THEN** ответ содержит: `response` (текст), `description` (описание), `processed_image_base64` = null, `processed_image_mime_type` = null
