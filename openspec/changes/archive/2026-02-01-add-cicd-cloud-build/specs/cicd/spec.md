## ADDED Requirements

### Requirement: Automatic deployment on push to main

Система SHALL автоматически деплоить master-agent в Cloud Run при push в ветку `main`.

#### Scenario: Successful auto-deploy
- **WHEN** разработчик делает push в ветку `main`
- **THEN** Cloud Build trigger запускает сборку и деплой
- **THEN** новая версия сервиса становится активной в Cloud Run

#### Scenario: Build failure notification
- **WHEN** сборка или деплой завершается с ошибкой
- **THEN** Cloud Build отображает статус FAILURE в консоли

### Requirement: Image tagging with SHORT_SHA

Система SHALL тегировать Docker образы с использованием `$SHORT_SHA` и `:latest` для трейсабилити.

#### Scenario: Image tagged with SHORT_SHA
- **WHEN** Cloud Build собирает образ
- **THEN** образ тегируется как `gcr.io/$PROJECT_ID/master-agent:$SHORT_SHA`
- **THEN** образ также тегируется как `gcr.io/$PROJECT_ID/master-agent:latest`

### Requirement: Cloud Build configuration file

Проект SHALL содержать файл `cloudbuild.yaml` в корне репозитория с конфигурацией CI/CD pipeline.

#### Scenario: cloudbuild.yaml exists
- **WHEN** Cloud Build trigger срабатывает
- **THEN** используется конфигурация из `cloudbuild.yaml`

### Requirement: Substitution variables

Конфигурация cloudbuild.yaml SHALL использовать substitution variables для `_REGION` и `_SERVICE_NAME`.

#### Scenario: Variables substituted
- **WHEN** Cloud Build выполняет steps
- **THEN** `${_SERVICE_NAME}` заменяется на `master-agent`
- **THEN** `${_REGION}` заменяется на `europe-west4`

### Requirement: Secret injection

Деплой SHALL использовать секреты из Secret Manager для ANTHROPIC_API_KEY.

#### Scenario: Secret mounted at deploy
- **WHEN** Cloud Build выполняет `gcloud run deploy`
- **THEN** секрет ANTHROPIC_API_KEY монтируется как environment variable

### Requirement: Manual deploy fallback

Скрипт `deploy-agent.sh` SHALL оставаться функциональным для ручного деплоя.

#### Scenario: Manual deploy works
- **WHEN** разработчик запускает `./deploy-agent.sh`
- **THEN** деплой выполняется успешно независимо от Cloud Build trigger

### Requirement: GitHub connection via Console

GitHub connection для Cloud Build trigger SHALL создаваться через GCP Console (не через CLI).

#### Scenario: Trigger creation
- **WHEN** настраивается Cloud Build trigger
- **THEN** GitHub репозиторий подключается через Console UI
