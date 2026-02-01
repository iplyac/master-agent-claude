## Why

Сейчас деплой master-agent выполняется вручную через `./deploy-agent.sh`. Это создает риск забыть задеплоить изменения и замедляет процесс разработки. Нужен автоматический CI/CD через Cloud Build triggers, как уже настроено для telegram-bot.

## What Changes

- Добавить `cloudbuild.yaml` с конфигурацией сборки и деплоя
- Создать Cloud Build trigger, срабатывающий при push в main ветку
- Логика деплоя переносится из `deploy-agent.sh` в `cloudbuild.yaml`

## Capabilities

### New Capabilities

- `cicd`: Автоматический CI/CD pipeline через Cloud Build triggers. Покрывает: конфигурацию cloudbuild.yaml, настройку триггера, автоматический деплой при push.

### Modified Capabilities

- `deployment`: Требования к деплою меняются — теперь деплой выполняется автоматически через Cloud Build, а не вручную через скрипт.

## Impact

- Новый файл: `cloudbuild.yaml`
- Скрипт `deploy-agent.sh` остается для локального/ручного деплоя
- Требуется настройка Cloud Build trigger в GCP Console или через gcloud
- Сервисный аккаунт Cloud Build должен иметь права на деплой в Cloud Run
