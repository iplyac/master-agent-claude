## 1. Зависимости и конфигурация

- [x] 1.1 Добавить `google-cloud-storage>=2.18.0` в `requirements.txt`
- [x] 1.2 Добавить функцию `get_gcs_bucket_name()` в `agent/config.py` (читает `GCS_BUCKET_NAME`, дефолт `master-agent-images`)

## 2. GCS клиент

- [x] 2.1 Создать `agent/gcs_client.py` с классом `GCSStorageClient`
- [x] 2.2 Реализовать метод `upload_original(image_bytes, mime_type, session_id) -> str | None` — сохраняет в `upload/{session_id}/{timestamp_ms}.{ext}`, возвращает GCS URI
- [x] 2.3 Реализовать метод `upload_processed(image_bytes, mime_type, session_id) -> str | None` — сохраняет в `processed/{session_id}/{timestamp_ms}.{ext}`, возвращает GCS URI
- [x] 2.4 Обернуть синхронные вызовы `google-cloud-storage` в `asyncio.get_event_loop().run_in_executor(None, ...)` для неблокирующего I/O
- [x] 2.5 Добавить маппинг MIME-тип → расширение (`image/jpeg` → `jpg`, `image/png` → `png`, `image/gif` → `gif`, `image/webp` → `webp`, fallback → `bin`)
- [x] 2.6 Ошибки логировать через `logger.warning(...)`, не пробрасывать (fire-and-forget)

## 3. Интеграция с MessageProcessor

- [x] 3.1 Добавить опциональный параметр `gcs_client: GCSStorageClient | None = None` в `__init__` класса `MessageProcessor` в `agent/processor.py`
- [x] 3.2 В методе `process_image()` вызвать `gcs_client.upload_original()` перед обработкой (если `gcs_client` не None)
- [x] 3.3 В методе `process_image()` вызвать `gcs_client.upload_processed()` после получения обработанного изображения от модели (если есть `processed_image_base64`)

## 4. Инициализация в app.py

- [x] 4.1 В `app.py` инициализировать `GCSStorageClient` если `get_gcs_bucket_name()` возвращает значение
- [x] 4.2 Передать `gcs_client` при создании `MessageProcessor`

## 5. IAM и деплой

- [x] 5.1 Убедиться что сервисный аккаунт Cloud Run имеет роль `roles/storage.objectCreator` на бакет `master-agent-images`
- [x] 5.2 Добавить `GCS_BUCKET_NAME=master-agent-images` в переменные окружения Cloud Run (или `.env` для локальной разработки)
- [x] 5.3 Добавить `GCS_BUCKET_NAME` в `.env.example`

## 6. Тесты

- [x] 6.1 Создать `tests/test_gcs_client.py` с юнит-тестами для `GCSStorageClient` (mock `google.cloud.storage.Client`)
- [x] 6.2 Добавить тест: оригинал загружается в `upload/` при вызове `process_image()`
- [x] 6.3 Добавить тест: обработанное изображение загружается в `processed/` при наличии `processed_image_base64`
- [x] 6.4 Добавить тест: ошибка GCS не влияет на ответ `process_image()`
- [x] 6.5 Добавить тест: если `gcs_client=None`, загрузки нет (backward compatibility)
