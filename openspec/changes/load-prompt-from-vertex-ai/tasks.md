## 1. Config

- [x] 1.1 Добавить функцию `get_prompt_id()` в `agent/config.py`

## 2. Prompt Loader

- [x] 2.1 Создать функцию `load_prompt_from_vertex_ai()` в `agent/adk_agent.py`
- [x] 2.2 Обновить `create_agent()` для использования загруженного промпта

## 3. Integration

- [x] 3.1 Вызвать загрузку промпта в `lifespan` в `app.py`
- [x] 3.2 Передать загруженный промпт в `create_agent()`

## 4. Testing

- [x] 4.1 Протестировать загрузку промпта локально
- [x] 4.2 Протестировать fallback при отсутствии AGENT_PROMPT_ID

## 5. Deploy

- [x] 5.1 Добавить `AGENT_PROMPT_ID` в cloudbuild.yaml
- [x] 5.2 Задеплоить обновлённый master-agent
- [x] 5.3 Проверить что агент использует промпт из Vertex AI
