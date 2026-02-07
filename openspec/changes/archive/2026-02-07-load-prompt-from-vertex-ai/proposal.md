## Why

Системный промпт агента сейчас захардкожен в коде. Чтобы изменить его, нужно деплоить новую версию. Vertex AI Prompt Management позволяет управлять промптами централизованно и обновлять их без редеплоя.

## What Changes

- Добавить загрузку системного промпта из Vertex AI Prompt Management при старте сервиса
- Использовать prompt resource ID из env variable `AGENT_PROMPT_ID`
- Fallback на `DEFAULT_INSTRUCTION` если промпт не найден или недоступен

## Capabilities

### New Capabilities
- `prompt-management`: Интеграция с Vertex AI Prompt Management для загрузки системного промпта

### Modified Capabilities
(none)

## Impact

- **Code**: `agent/adk_agent.py` — добавить загрузку промпта из Vertex AI
- **Dependencies**: Может потребоваться `google-cloud-aiplatform` SDK
- **Config**: Новый env var `AGENT_PROMPT_ID` с resource ID промпта
- **Startup**: Небольшое увеличение времени запуска (один API call)
