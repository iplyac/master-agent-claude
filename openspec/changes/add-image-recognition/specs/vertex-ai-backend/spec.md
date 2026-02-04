## ADDED Requirements

### Requirement: Image messages share session context

Изображения SHALL обрабатываться в том же контексте сессии, что и текстовые и голосовые сообщения.

#### Scenario: Image description via Vertex AI
- **WHEN** поступает изображение
- **THEN** MediaClient описывает изображение через Vertex AI multimodal API

#### Scenario: Image response through ADK Runner
- **WHEN** описание изображения получено
- **THEN** описание передаётся в ADK Runner для генерации ответа с сохранением контекста сессии

#### Scenario: Shared context between text, voice and images
- **WHEN** пользователь отправляет текстовое сообщение, затем изображение
- **THEN** обработка изображения видит историю текстовых сообщений в сессии
