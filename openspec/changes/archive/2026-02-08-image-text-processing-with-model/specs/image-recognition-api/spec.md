## MODIFIED Requirements

### Requirement: Response format

Ответ endpoint SHALL содержать стандартизированный JSON формат с опциональными полями для обработанного изображения.

#### Scenario: Success response structure
- **WHEN** запрос успешен
- **THEN** ответ содержит поля: `response` (текст ответа), `description` (описание изображения), `processed_image_base64` (base64 обработанного изображения или null), `processed_image_mime_type` (MIME тип обработанного изображения или null)
