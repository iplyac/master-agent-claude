## 1. Конфигурация

- [x] 1.1 Добавить `get_docling_agent_url() -> Optional[str]` в `agent/config.py` (читает `DOCLING_AGENT_URL`)
- [x] 1.2 Добавить `get_docling_gcs_bucket() -> str` в `agent/config.py` (читает `GCS_DOCLING_BUCKET`, дефолт `docling-documents`)
- [x] 1.3 Добавить `DOCLING_AGENT_URL` и `GCS_DOCLING_BUCKET` в `.env.example`

## 2. Pydantic модели

- [x] 2.1 Добавить `DocumentRequest` в `agent/models.py`: поля `conversation_id: str`, `document_base64: str`, `mime_type: str`, `filename: str`, `metadata: Optional[RequestMetadata]`
- [x] 2.2 Добавить `DocumentMetadata` в `agent/models.py`: поля `format: str`, `pages: Optional[int]`, `tables_found: Optional[int]`, `images_found: Optional[int]`, `processing_time_ms: Optional[int]`
- [x] 2.3 Добавить `DocumentResponse` в `agent/models.py`: поля `content: str`, `metadata: Optional[DocumentMetadata]`, `gcs_uri: str`

## 3. Docling клиент

- [x] 3.1 Создать `agent/docling_client.py` с классом `DoclingClient`
- [x] 3.2 Реализовать `__init__(self, agent_url: str)` — принимает URL docling агента
- [x] 3.3 Реализовать приватный метод `_get_auth_header(self) -> dict` — возвращает `{"Authorization": "Bearer <id_token>"}` для Cloud Run URL, пустой dict для localhost
- [x] 3.4 Реализовать `async process_document(self, gcs_uri: str, mime_type: str, filename: str) -> dict` — POST к `/api/process-document` с `{"document_url": gcs_uri, "mime_type": mime_type, "output_format": "markdown"}` и таймаутом 310s
- [x] 3.5 Обрабатывать статус-коды ответа: 200 → вернуть dict, 4xx/5xx → выбросить `RuntimeError` с сообщением, timeout → выбросить `TimeoutError`

## 4. GCS для docling бакета

- [x] 4.1 В `agent/gcs_client.py` добавить метод `upload_document(self, data: bytes, conversation_id: str, filename: str) -> str` — загружает в `input/{conversation_id}/{timestamp_ms}_{filename}`, возвращает GCS URI (не fire-and-forget — пробрасывает ошибку)

## 5. Endpoint в app.py

- [x] 5.1 Импортировать `DocumentRequest`, `DocumentResponse`, `DocumentMetadata` и `DoclingClient` в `app.py`
- [x] 5.2 Добавить `get_docling_agent_url`, `get_docling_gcs_bucket` в импорт из `agent.config`
- [x] 5.3 В `lifespan()`: инициализировать `GCSStorageClient(get_docling_gcs_bucket())` как `docling_gcs_client` и `DoclingClient(get_docling_agent_url())` как `docling_client` (если URL задан), сохранить в `app.state`
- [x] 5.4 Добавить `POST /api/document` endpoint
- [x] 5.5 Обработать ошибки: GCS → 500, DoclingClient RuntimeError → 502, TimeoutError → 504, прочие → 500

## 6. IAM и деплой

- [x] 6.1 Выдать SA мастер агента роль `roles/run.invoker` на docling агент сервис в Cloud Run
- [x] 6.2 Выдать SA мастер агента роль `roles/storage.objectCreator` на бакет `docling-documents`
- [x] 6.3 Добавить `DOCLING_AGENT_URL=https://docling-agent-xxxx-ew.a.run.app` в переменные окружения Cloud Run мастер агента

## 7. Тесты

- [x] 7.1 Создать `tests/test_docling_client.py` с юнит-тестами для `DoclingClient` (mock httpx)
- [x] 7.2 Тест: успешный вызов возвращает `content` и `metadata`
- [x] 7.3 Тест: non-200 от docling агента → `RuntimeError`
- [x] 7.4 Тест: таймаут → `TimeoutError`
- [x] 7.5 Тест: localhost URL → нет Authorization header
- [x] 7.6 Создать `tests/test_document_api.py` с тестами endpoint `POST /api/document`
- [x] 7.7 Тест: успешный запрос возвращает 200 с `content`
- [x] 7.8 Тест: отсутствие `document_base64` → 400
- [x] 7.9 Тест: неподдерживаемый MIME type → 400
- [x] 7.10 Тест: `DOCLING_AGENT_URL` не задан → 503
- [x] 7.11 Тест: docling агент вернул ошибку → 502
- [x] 7.12 Тест: GCS upload упал → 500, docling не вызывается
