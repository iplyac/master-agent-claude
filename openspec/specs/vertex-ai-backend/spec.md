### Requirement: Vertex AI LLM backend

Сервис SHALL использовать Vertex AI API (aiplatform.googleapis.com) для доступа к Gemini моделям вместо Google AI API.

#### Scenario: LLM request через Vertex AI
- **WHEN** поступает запрос на обработку сообщения
- **THEN** ADK отправляет запрос к Vertex AI endpoint с указанным project и location

#### Scenario: Аутентификация через ADC
- **WHEN** сервис запускается на Cloud Run
- **THEN** используются Application Default Credentials от attached service account

### Requirement: InMemorySessionService для хранения сессий

Сервис SHALL использовать `InMemorySessionService` из ADK для управления сессиями в рамках одного контейнера.

#### Scenario: Создание сессии
- **WHEN** поступает первое сообщение от нового conversation_id
- **THEN** InMemorySessionService создаёт новую сессию в памяти

#### Scenario: Восстановление истории в рамках сессии
- **WHEN** поступает сообщение от существующего conversation_id
- **THEN** InMemorySessionService загружает историю событий из памяти

### Requirement: Конфигурация через environment variables

Сервис SHALL принимать настройки Vertex AI через переменные окружения.

#### Scenario: Enable Vertex AI backend
- **WHEN** переменная GOOGLE_GENAI_USE_VERTEXAI=true установлена
- **THEN** ADK использует Vertex AI вместо Google AI API

#### Scenario: Project ID из env
- **WHEN** переменная GOOGLE_CLOUD_PROJECT установлена
- **THEN** сервис использует её для настройки Vertex AI client

#### Scenario: Location из env
- **WHEN** переменная GOOGLE_CLOUD_LOCATION установлена
- **THEN** сервис использует её как region для Vertex AI (по умолчанию europe-west4)

### Requirement: Отсутствие зависимости от API key

Сервис SHALL работать без GOOGLE_API_KEY при использовании Vertex AI backend.

#### Scenario: Запуск без API key
- **WHEN** GOOGLE_API_KEY не установлен
- **AND** настроен Vertex AI backend
- **THEN** сервис успешно запускается и обрабатывает запросы
