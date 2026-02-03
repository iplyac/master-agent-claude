## ADDED Requirements

### Requirement: Vertex AI LLM backend

Сервис SHALL использовать Vertex AI API (aiplatform.googleapis.com) для доступа к Gemini моделям вместо Google AI API.

#### Scenario: LLM request через Vertex AI
- **WHEN** поступает запрос на обработку сообщения
- **THEN** ADK отправляет запрос к Vertex AI endpoint с указанным project и location

#### Scenario: Аутентификация через ADC
- **WHEN** сервис запускается на Cloud Run
- **THEN** используются Application Default Credentials от attached service account

### Requirement: VertexAiSessionService для хранения сессий

Сервис SHALL использовать встроенный `VertexAiSessionService` из ADK для управления сессиями.

#### Scenario: Создание сессии
- **WHEN** поступает первое сообщение от нового conversation_id
- **THEN** VertexAiSessionService создаёт новую сессию в managed storage

#### Scenario: Восстановление истории
- **WHEN** поступает сообщение от существующего conversation_id
- **THEN** VertexAiSessionService загружает историю событий из managed storage

### Requirement: Конфигурация через environment variables

Сервис SHALL принимать настройки Vertex AI через переменные окружения.

#### Scenario: Project ID из env
- **WHEN** переменная GCP_PROJECT_ID установлена
- **THEN** сервис использует её для настройки Vertex AI client

#### Scenario: Location из env
- **WHEN** переменная GCP_LOCATION установлена
- **THEN** сервис использует её как region для Vertex AI (по умолчанию europe-west4)

### Requirement: Отсутствие зависимости от API key

Сервис SHALL работать без GOOGLE_API_KEY при использовании Vertex AI backend.

#### Scenario: Запуск без API key
- **WHEN** GOOGLE_API_KEY не установлен
- **AND** настроен Vertex AI backend
- **THEN** сервис успешно запускается и обрабатывает запросы
