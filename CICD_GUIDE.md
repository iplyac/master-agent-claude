# CI/CD Guide для Master-Agent

Инструкция по настройке автоматического деплоя master-agent через Google Cloud Build.

## Обзор

```
GitHub push (main) → Cloud Build trigger → Build image → Deploy to Cloud Run
```

## 1. Создать cloudbuild.yaml

```yaml
steps:
  # Step 1: Build Docker image
  - name: 'gcr.io/cloud-builders/docker'
    args:
      - 'build'
      - '-t'
      - 'gcr.io/$PROJECT_ID/${_SERVICE_NAME}:latest'
      - '-t'
      - 'gcr.io/$PROJECT_ID/${_SERVICE_NAME}:$SHORT_SHA'
      - '.'

  # Step 2: Push image to Container Registry
  - name: 'gcr.io/cloud-builders/docker'
    args:
      - 'push'
      - 'gcr.io/$PROJECT_ID/${_SERVICE_NAME}'
      - '--all-tags'

  # Step 3: Deploy to Cloud Run
  - name: 'gcr.io/google.com/cloudsdktool/cloud-sdk'
    entrypoint: 'gcloud'
    args:
      - 'run'
      - 'deploy'
      - '${_SERVICE_NAME}'
      - '--image'
      - 'gcr.io/$PROJECT_ID/${_SERVICE_NAME}:$SHORT_SHA'
      - '--region'
      - '${_REGION}'
      - '--platform'
      - 'managed'
      - '--ingress'
      - 'all'  # Публичный доступ для telegram-bot
      - '--set-secrets'
      - 'ANTHROPIC_API_KEY=ANTHROPIC_API_KEY:latest'
      # Добавь другие secrets по необходимости

# Substitution variables
substitutions:
  _REGION: 'europe-west4'
  _SERVICE_NAME: 'master-agent'

# Build options
options:
  logging: CLOUD_LOGGING_ONLY

# Images to push
images:
  - 'gcr.io/$PROJECT_ID/${_SERVICE_NAME}:latest'
  - 'gcr.io/$PROJECT_ID/${_SERVICE_NAME}:$SHORT_SHA'
```

## 2. Настроить IAM permissions

Cloud Build service account нужны права для деплоя.

```bash
PROJECT_ID="gen-lang-client-0741140892"
PROJECT_NUMBER=$(gcloud projects describe $PROJECT_ID --format='value(projectNumber)')
CLOUD_BUILD_SA="${PROJECT_NUMBER}@cloudbuild.gserviceaccount.com"

# ⚠️ ВАЖНО: Используй --condition=None если в проекте есть IAM conditions
gcloud projects add-iam-policy-binding $PROJECT_ID \
  --member="serviceAccount:$CLOUD_BUILD_SA" \
  --role="roles/run.admin" \
  --condition=None

gcloud projects add-iam-policy-binding $PROJECT_ID \
  --member="serviceAccount:$CLOUD_BUILD_SA" \
  --role="roles/secretmanager.secretAccessor" \
  --condition=None

gcloud projects add-iam-policy-binding $PROJECT_ID \
  --member="serviceAccount:$CLOUD_BUILD_SA" \
  --role="roles/iam.serviceAccountUser" \
  --condition=None
```

**Проверка:**
```bash
gcloud projects get-iam-policy $PROJECT_ID \
  --flatten="bindings[].members" \
  --filter="bindings.members:$CLOUD_BUILD_SA" \
  --format="value(bindings.role)"
```

Должно показать:
- `roles/cloudbuild.builds.builder`
- `roles/run.admin`
- `roles/secretmanager.secretAccessor`
- `roles/iam.serviceAccountUser`

## 3. Создать Cloud Build trigger (через Console)

⚠️ **GitHub connection нельзя создать через CLI** — только через Console.

1. Открой: https://console.cloud.google.com/cloud-build/triggers?project=gen-lang-client-0741140892

2. **Connect Repository:**
   - Нажми "Connect Repository"
   - Выбери GitHub → авторизуй
   - Найди репозиторий master-agent

3. **Create Trigger:**
   - Name: `master-agent-main`
   - Event: Push to a branch
   - Branch: `^main$`
   - Configuration: Cloud Build configuration file
   - Location: `cloudbuild.yaml`

4. **Substitution variables** (если нужны):
   - `_REGION` = `europe-west4` (или оставь дефолт)

## 4. Известные проблемы и решения

### Проблема 1: IAM binding fails без --condition=None

**Ошибка:**
```
ERROR: Adding a binding without specifying a condition to a policy containing conditions is prohibited
```

**Решение:** Добавь `--condition=None` к команде.

### Проблема 2: Secret содержит лишние символы

Если secret в Secret Manager содержит multi-line или extra formatting:

**Проблема:** `gcloud secrets versions access` возвращает больше данных чем ожидается.

**Решение:** Извлекай чистое значение через grep/regex:
```bash
# Пример для API key
API_KEY=$(gcloud secrets versions access latest --secret=ANTHROPIC_API_KEY | tr -d '\n\r ')
```

### Проблема 3: Step fails с exit code из-за set -e

Если используешь bash step с `set -e`, любая команда с non-zero exit (включая `grep -q` когда не находит) убьёт весь step.

**Решение:**
- Убери `set -e`
- Добавь `|| true` после команд которые могут fail
- Добавь `exit 0` в конце

### Проблема 4: Build succeeds но сервис не работает

**Проверь:**
1. Secrets подключены: `--set-secrets` в gcloud run deploy
2. Ingress настроен: `--ingress=all` для публичного доступа
3. Порт правильный: Cloud Run использует `$PORT` (обычно 8080)

## 5. Тестирование

После настройки:

```bash
# Сделай тестовый коммит
git commit --allow-empty -m "Test CI/CD pipeline"
git push origin main

# Проверь билд
gcloud builds list --project=gen-lang-client-0741140892 --limit=1

# Проверь логи билда
gcloud builds log <BUILD_ID> --project=gen-lang-client-0741140892
```

## 6. Полезные команды

```bash
# Список triggers
gcloud builds triggers list --project=gen-lang-client-0741140892

# Последние билды
gcloud builds list --project=gen-lang-client-0741140892 --limit=5

# Статус сервиса
gcloud run services describe master-agent \
  --region=europe-west4 \
  --project=gen-lang-client-0741140892

# Логи сервиса
gcloud run services logs read master-agent \
  --region=europe-west4 \
  --project=gen-lang-client-0741140892 \
  --limit=50
```

## Чеклист

- [ ] `cloudbuild.yaml` создан в корне репозитория
- [ ] IAM permissions настроены для Cloud Build SA
- [ ] GitHub репозиторий подключен к Cloud Build
- [ ] Trigger создан для main branch
- [ ] Secrets существуют в Secret Manager
- [ ] Тестовый push прошёл успешно
- [ ] Сервис отвечает на health check
