## Context

Мастер агент — FastAPI сервис в Cloud Run, который принимает запросы от Telegram бота. Docling агент — отдельный Cloud Run сервис (`--ingress=internal`, `--no-allow-unauthenticated`) для тяжёлой обработки документов через библиотеку Docling. Взаимодействие: мастер агент загружает документ в GCS `docling-documents/input/`, затем вызывает docling агент с GCS URI. Docling агент забирает файл из GCS сам, обрабатывает и возвращает контент.

Существующий `GCSStorageClient` (из change `gcs-image-storage`) уже умеет загружать байты в GCS — используем его повторно с другим бакетом.

## Goals / Non-Goals

**Goals:**
- Принять документ (base64) + метаданные от Telegram бота через `POST /api/document`
- Загрузить оригинал в `gs://docling-documents/input/{conversation_id}/{timestamp_ms}_{filename}`
- Аутентифицированный HTTP-вызов к docling агенту с GCS URI
- Вернуть извлечённый контент (markdown) клиенту

**Non-Goals:**
- Асинхронная обработка / очереди (синхронный request-response)
- Кэширование результатов (docling агент сам опционально сохраняет в GCS)
- Поддержка нескольких output format (используем дефолтный markdown)
- Хранение результата в GCS на стороне мастер агента (docling агент делает это сам при наличии `GCS_RESULT_BUCKET`)

## Decisions

### 1. Cloud Run IAM auth через ID Token

**Выбор:** При вызове docling агента добавляем заголовок `Authorization: Bearer <id_token>`. ID token получаем через `google.auth.transport.requests` + `google.oauth2.id_token.fetch_id_token(request, audience=DOCLING_AGENT_URL)`.

**Почему:** Docling агент задеплоен с `--no-allow-unauthenticated`. Стандартный подход для Cloud Run to Cloud Run auth — ID token с audience = URL сервиса.

**Альтернатива:** Убрать аутентификацию с docling агента и открыть его через API Gateway — отклонено, снижает безопасность.

**Локальная разработка:** Если `DOCLING_AGENT_URL` не задан — `DoclingClient` не создаётся, endpoint возвращает 503. Для локальной разработки с докинг агентом на localhost токен не нужен (skip auth если URL содержит localhost/127.0.0.1).

---

### 2. Отдельный экземпляр GCSStorageClient для docling бакета

**Выбор:** В `app.py` создаём второй `GCSStorageClient(bucket_name=get_docling_gcs_bucket())` рядом с первым (для `master-agent-images`).

**Почему:** `GCSStorageClient` уже параметризован по `bucket_name`. Дублирование экземпляра проще, чем усложнение API.

**Альтернатива:** Добавить метод `upload_to_bucket(bucket, ...)` в базовый клиент — отклонено, не нужна лишняя абстракция.

---

### 3. Именование объектов в GCS

**Схема:** `input/{conversation_id}/{timestamp_ms}_{filename}`

Пример: `input/tg-123456/1700000000000_report.pdf`

**Почему:** `conversation_id` группирует по пользователю; `timestamp_ms` + оригинальный filename даёт уникальность и читаемость при дебаге.

---

### 4. Синхронный вызов docling агента

**Выбор:** `httpx.AsyncClient` с таймаутом 310 секунд (чуть больше чем у docling агента 300s).

**Почему:** Docling обработка занимает секунды-минуты. Telegram бот ждёт ответа. Асинхронный (webhook/queue) паттерн усложнит архитектуру без явной необходимости.

**Риск:** Cloud Run мастер агент имеет свой request timeout. Если он меньше 310s — запрос упадёт. Нужно убедиться что timeout Cloud Run >= 310s.

---

### 5. Новый модуль `agent/docling_client.py`

**Выбор:** Отдельный класс `DoclingClient` с методом `process_document(gcs_uri, mime_type, filename)`.

**Почему:** Изоляция HTTP-логики, мокирование в тестах, одно место для настройки timeout/retry.

## Risks / Trade-offs

- **[Риск] Timeout мастер агента < 310s** → Митигация: задокументировать в tasks, убедиться что Cloud Run timeout мастер агента >= 360s
- **[Риск] docling агент недоступен** → Митигация: возвращаем 503 с понятным сообщением; не блокируем остальные endpoints
- **[Риск] ID token истекает (1h TTL)** → Митигация: `fetch_id_token` всегда получает свежий токен — вызывается при каждом запросе, не кэшируется
- **[Trade-off] Синхронный вызов** — долгие документы держат соединение открытым; приемлемо для MVP, можно асинхронизировать позже
- **[Риск] Большие файлы** → Митигация: валидация на стороне мастер агента (ограничение размера base64), docling агент тоже проверяет (50MB по умолчанию)
