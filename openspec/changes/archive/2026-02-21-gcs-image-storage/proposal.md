## Why

Сейчас изображения обрабатываются полностью в памяти и нигде не сохраняются — после обработки они теряются. Нужно персистентное хранилище для аудита, повторного использования и отладки.

## What Changes

- Добавить `GCSStorageClient` — клиент для загрузки файлов в Google Cloud Storage
- При получении изображения сохранять оригинал в бакет `master-agent-images/upload/`
- После обработки изображения моделью сохранять результат в `master-agent-images/processed/`
- Имена файлов формировать по шаблону `{session_id}/{timestamp}_{filename}`
- Добавить `google-cloud-storage` в `requirements.txt`
- Конфигурация бакета через переменную окружения `GCS_BUCKET_NAME` (дефолт: `master-agent-images`)

## Capabilities

### New Capabilities
- `gcs-image-storage`: Загрузка оригинальных и обработанных изображений в GCS бакет с разбивкой по папкам `upload/` и `processed/`

### Modified Capabilities
<!-- нет -->

## Impact

- **Новая зависимость**: `google-cloud-storage` → добавить в `requirements.txt`
- **Новый модуль**: `agent/gcs_client.py` — клиент для работы с GCS
- **Изменённый модуль**: `agent/processor.py` — вызов GCS клиента в `process_image()`
- **Изменённый модуль**: `agent/config.py` — новая функция `get_gcs_bucket_name()`
- **Изменённый модуль**: `app.py` — инициализация GCS клиента и передача в `MessageProcessor`
- **IAM**: сервисный аккаунт Cloud Run должен иметь роль `roles/storage.objectCreator` на бакет `master-agent-images`
