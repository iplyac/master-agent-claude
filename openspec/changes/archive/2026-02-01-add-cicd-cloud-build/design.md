## Context

Текущий процесс деплоя master-agent:
1. Разработчик вручную запускает `./deploy-agent.sh`
2. Скрипт использует `gcloud builds submit` для сборки образа
3. Затем `gcloud run deploy` для деплоя в Cloud Run

Проблемы:
- Легко забыть задеплоить после push
- Нет автоматической проверки что код в main соответствует production
- Ручной процесс замедляет итерации

Telegram-bot уже использует Cloud Build triggers для автоматического деплоя.

Референс: `CICD_GUIDE.md` содержит готовые шаблоны и команды.

## Goals / Non-Goals

**Goals:**
- Автоматический деплой при push в main ветку
- Сохранить возможность ручного деплоя через скрипт
- Использовать тот же подход что и telegram-bot для консистентности

**Non-Goals:**
- CI проверки (тесты, линтинг) — можно добавить позже
- Деплой в staging/preview environments
- Rollback автоматизация

## Decisions

### 1. Cloud Build trigger на push в main

**Решение:** Создать trigger, срабатывающий при push в `main` ветку.

**Ограничение:** GitHub connection нельзя создать через CLI — только через Console.

### 2. Структура cloudbuild.yaml

**Решение:** Три шага — build, push, deploy. Используем substitution variables для гибкости:

```yaml
steps:
  - name: 'gcr.io/cloud-builders/docker'
    args: ['build', '-t', 'gcr.io/$PROJECT_ID/${_SERVICE_NAME}:latest',
           '-t', 'gcr.io/$PROJECT_ID/${_SERVICE_NAME}:$SHORT_SHA', '.']

  - name: 'gcr.io/cloud-builders/docker'
    args: ['push', 'gcr.io/$PROJECT_ID/${_SERVICE_NAME}', '--all-tags']

  - name: 'gcr.io/google.com/cloudsdktool/cloud-sdk'
    entrypoint: 'gcloud'
    args: ['run', 'deploy', '${_SERVICE_NAME}', ...]

substitutions:
  _REGION: 'europe-west4'
  _SERVICE_NAME: 'master-agent'
```

### 3. Теги образов

**Решение:** Двойной тег — `:latest` и `:$SHORT_SHA` для трейсабилити.

`$SHORT_SHA` — встроенная переменная Cloud Build (первые 7 символов commit SHA).

### 4. Секреты

**Решение:** Использовать `--set-secrets` для ANTHROPIC_API_KEY:

```yaml
- '--set-secrets'
- 'ANTHROPIC_API_KEY=ANTHROPIC_API_KEY:latest'
```

### 5. IAM permissions

**Решение:** Cloud Build SA требует роли:
- `roles/run.admin`
- `roles/secretmanager.secretAccessor`
- `roles/iam.serviceAccountUser`

**Важно:** Использовать `--condition=None` при добавлении IAM bindings если в проекте есть conditions.

## Risks / Trade-offs

**[Risk] Cloud Build сервисный аккаунт без прав**
→ Mitigation: Команды для настройки IAM есть в CICD_GUIDE.md

**[Risk] Ошибка в cloudbuild.yaml ломает деплой**
→ Mitigation: deploy-agent.sh остается как fallback для ручного деплоя

**[Risk] IAM binding fails без --condition=None**
→ Mitigation: Всегда использовать `--condition=None` в командах

**[Trade-off] Нет проверок перед деплоем**
→ Сознательное решение для MVP. Тесты можно добавить как дополнительный step позже.
