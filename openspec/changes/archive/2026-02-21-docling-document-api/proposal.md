## Why

Telegram бот умеет пересылать документы (PDF, DOCX, XLSX и т.д.), но у мастер агента нет endpoint для их приёма и обработки. Нужен pipeline: принять документ → сохранить в GCS → передать docling агенту (отдельный Cloud Run сервис) → вернуть структурированный контент.

## What Changes

- Добавить `POST /api/document` endpoint в мастер агент
- Документ (base64) сохраняется в GCS бакет `docling-documents` в папку `input/{conversation_id}/{timestamp_ms}_{filename}`
- Мастер агент вызывает docling агент (Cloud Run) через HTTP, передавая GCS URI (`gs://docling-documents/input/...`)
- Docling агент обрабатывает документ через Docling library и возвращает текст/markdown
- Добавить `DoclingClient` — обёртку для HTTP-вызовов к docling агенту с Cloud Run IAM auth (ID token)
- Добавить новые Pydantic модели: `DocumentRequest`, `DocumentResponse`
- Добавить новые конфиг-переменные: `DOCLING_AGENT_URL`, `GCS_DOCLING_BUCKET`
- Переиспользовать `GCSStorageClient` для загрузки в `docling-documents` бакет

## Capabilities

### New Capabilities
- `document-processing-api`: Приём документа от Telegram, загрузка в GCS и вызов docling агента для извлечения контента

### Modified Capabilities
<!-- нет — gcs-image-storage работает независимо, только другой бакет -->

## Impact

- **Новый модуль**: `agent/docling_client.py` — HTTP клиент к docling агенту с ID token auth
- **Изменённый модуль**: `agent/models.py` — новые модели `DocumentRequest`, `DocumentResponse`
- **Изменённый модуль**: `agent/config.py` — `get_docling_agent_url()`, `get_docling_gcs_bucket()`
- **Изменённый модуль**: `app.py` — новый endpoint `/api/document`, инициализация `DoclingClient`
- **Изменённый модуль**: `agent/gcs_client.py` — сделать `bucket_name` параметром при вызове (уже так, просто создаём второй экземпляр с другим бакетом)
- **Зависимости**: `httpx` уже есть; `google-auth` уже транзитивная зависимость (через google-cloud-storage)
- **IAM**: SA Cloud Run мастер агента нужна роль `roles/run.invoker` на docling агент; `roles/storage.objectCreator` на бакет `docling-documents`
- **Env vars**: `DOCLING_AGENT_URL`, `GCS_DOCLING_BUCKET` (дефолт: `docling-documents`)
