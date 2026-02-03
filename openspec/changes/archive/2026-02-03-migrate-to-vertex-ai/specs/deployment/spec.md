## ADDED Requirements

### Requirement: Vertex AI environment variables

Сервис SHALL получать конфигурацию Vertex AI через переменные окружения.

#### Scenario: GCP_PROJECT_ID configured
- **WHEN** выполняется деплой
- **THEN** переменная GCP_PROJECT_ID установлена с ID проекта

#### Scenario: GCP_LOCATION configured
- **WHEN** выполняется деплой
- **THEN** переменная GCP_LOCATION установлена (europe-west4)

### Requirement: Service account IAM role

Service account Cloud Run SHALL иметь роль `Vertex AI User`.

#### Scenario: IAM role assigned
- **WHEN** сервис обращается к Vertex AI API
- **THEN** авторизация проходит успешно через attached service account

## REMOVED Requirements

### Requirement: GOOGLE_API_KEY secret

**Reason**: Аутентификация переходит на service account через ADC вместо API key.

**Migration**: Убрать `--set-secrets="GOOGLE_API_KEY=..."` из команды деплоя. Добавить IAM роль `Vertex AI User` к service account.
