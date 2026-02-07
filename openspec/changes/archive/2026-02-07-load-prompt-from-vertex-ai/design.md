## Context

Системный промпт определён в `agent/adk_agent.py` как `DEFAULT_INSTRUCTION`. Vertex AI Prompt Management позволяет хранить и версионировать промпты в облаке.

Prompt resource:
- Project: `gen-lang-client-0741140892`
- Location: `europe-west4`
- Prompt ID: `5914177388295487488`

## Goals / Non-Goals

**Goals:**
- Загружать системный промпт из Vertex AI Prompt Management при старте
- Fallback на default если Vertex AI недоступен
- Конфигурация через env variable

**Non-Goals:**
- Hot-reload промпта без перезапуска
- Кеширование промпта между запросами

## Decisions

### Decision 1: Загрузка при старте в lifespan

**Выбор**: Загружать промпт один раз в `lifespan` функции app.py.

**Обоснование**: Промпт не меняется во время работы сервиса. Загрузка при старте минимизирует latency запросов.

### Decision 2: Использовать google-cloud-aiplatform SDK

**Выбор**: Использовать `aiplatform.Prompt.get()` для загрузки промпта.

**API**:
```python
from google.cloud import aiplatform

aiplatform.init(project=project_id, location=location)
prompt = aiplatform.Prompt.get(prompt_id)
instruction = prompt.prompt_data.system_instruction.parts[0].text
```

### Decision 3: Graceful fallback

**Выбор**: При ошибке загрузки использовать `DEFAULT_INSTRUCTION` и логировать warning.

**Обоснование**: Сервис должен запускаться даже если Vertex AI временно недоступен.

## Risks / Trade-offs

| Risk | Mitigation |
|------|------------|
| Vertex AI недоступен при старте | Fallback на default instruction + warning log |
| Увеличение времени cold start | Один API call ~100-500ms, приемлемо |
| Prompt ID изменился/удалён | Fallback + clear error message |
