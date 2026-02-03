### Requirement: Service name

Сервис SHALL деплоиться с именем `master-agent`.

#### Scenario: Service naming
- **WHEN** выполняется деплой
- **THEN** сервис создается/обновляется с именем `master-agent`

### Requirement: Public ingress

Сервис SHALL принимать публичный traffic (ingress=all).

#### Scenario: Public request accepted
- **WHEN** запрос приходит с любого IP
- **THEN** сервис обрабатывает запрос

### Requirement: Same region deployment

Сервис SHALL быть развёрнут в регионе `europe-west4` (совпадает с telegram-bot).

#### Scenario: Regional colocation
- **WHEN** оба сервиса в одном регионе
- **THEN** минимизируется latency между сервисами

### Requirement: Vertex AI environment variables

Сервис SHALL получать конфигурацию Vertex AI через переменные окружения.

#### Scenario: GOOGLE_GENAI_USE_VERTEXAI configured
- **WHEN** выполняется деплой
- **THEN** переменная GOOGLE_GENAI_USE_VERTEXAI=true установлена

#### Scenario: GOOGLE_CLOUD_PROJECT configured
- **WHEN** выполняется деплой
- **THEN** переменная GOOGLE_CLOUD_PROJECT установлена с ID проекта

#### Scenario: GOOGLE_CLOUD_LOCATION configured
- **WHEN** выполняется деплой
- **THEN** переменная GOOGLE_CLOUD_LOCATION установлена (europe-west4)

### Requirement: Service account IAM role

Service account Cloud Run SHALL иметь роль `Vertex AI User`.

#### Scenario: IAM role assigned
- **WHEN** сервис обращается к Vertex AI API
- **THEN** авторизация проходит успешно через attached service account
