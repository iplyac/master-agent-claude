## 1. Cloud Build Configuration

- [x] 1.1 Создать файл `cloudbuild.yaml` в корне репозитория (шаблон в CICD_GUIDE.md)
- [x] 1.2 Настроить step для сборки Docker образа с тегами `:latest` и `:$SHORT_SHA`
- [x] 1.3 Настроить step для push образа с `--all-tags`
- [x] 1.4 Настроить step для деплоя в Cloud Run с `--set-secrets=ANTHROPIC_API_KEY=ANTHROPIC_API_KEY:latest`
- [x] 1.5 Добавить substitution variables: `_REGION=europe-west4`, `_SERVICE_NAME=master-agent`

## 2. IAM Permissions

- [x] 2.1 Получить Cloud Build SA: `${PROJECT_NUMBER}@cloudbuild.gserviceaccount.com`
- [x] 2.2 Добавить роль `roles/run.admin` с `--condition=None`
- [x] 2.3 Добавить роль `roles/secretmanager.secretAccessor` с `--condition=None`
- [x] 2.4 Добавить роль `roles/iam.serviceAccountUser` с `--condition=None`
- [x] 2.5 Проверить permissions командой из CICD_GUIDE.md

## 3. Cloud Build Trigger (Console)

- [x] 3.1 Открыть Cloud Build Triggers в Console
- [x] 3.2 Connect Repository — подключить GitHub репозиторий master-agent
- [x] 3.3 Create Trigger с именем `master-agent-main`
- [x] 3.4 Настроить Event: Push to branch `^main$`
- [x] 3.5 Указать Configuration: `cloudbuild.yaml`

## 4. Secrets

- [x] 4.1 Проверить что секрет ANTHROPIC_API_KEY существует в Secret Manager
- [x] 4.2 Если нет — создать секрет с API ключом (использован GOOGLE_API_KEY)

## 5. Verification

- [ ] 5.1 Сделать тестовый push: `git commit --allow-empty -m "Test CI/CD" && git push`
- [ ] 5.2 Проверить билд: `gcloud builds list --limit=1`
- [ ] 5.3 Проверить что сервис отвечает на health check
- [ ] 5.4 Проверить что ручной деплой через `./deploy-agent.sh` работает
