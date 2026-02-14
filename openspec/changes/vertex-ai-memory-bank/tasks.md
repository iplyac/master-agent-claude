## 1. Configuration

- [x] 1.1 Add `get_agent_engine_id()` to `agent/config.py` — reads `AGENT_ENGINE_ID` env var, returns `Optional[str]`

## 2. Agent Setup

- [x] 2.1 Update `create_agent()` in `agent/adk_agent.py` — accept optional `tools` parameter; when Memory Bank is enabled, include `PreloadMemoryTool` in tools list

## 3. Session & Memory Services

- [x] 3.1 Update `app.py` lifespan — when `AGENT_ENGINE_ID` is set, create `VertexAiSessionService` and `VertexAiMemoryBankService` instead of `InMemorySessionService`; pass `memory_service` to Runner
- [x] 3.2 Add fallback logic — when `AGENT_ENGINE_ID` is not set, use `InMemorySessionService` without memory_service (existing behavior)

## 4. Memory Integration in Processor

- [x] 4.1 Update `MessageProcessor.__init__()` — accept optional `memory_service` parameter (type `BaseMemoryService | None`)
- [x] 4.2 Update `MessageProcessor.process()` — after successful agent response, call `memory_service.add_session_to_memory(session)` if memory_service is configured
- [x] 4.3 Wire memory_service in `app.py` — pass to `MessageProcessor` constructor

## 5. Dependencies

- [x] 5.1 Verify/update `requirements.txt` — ensure `google-adk` version supports `VertexAiMemoryBankService`, `VertexAiSessionService`, and `PreloadMemoryTool`

## 6. Deployment

- [x] 6.1 Create Agent Engine instance via gcloud CLI or console and document the command
- [x] 6.2 Update `cloudbuild.yaml` or deploy script to pass `AGENT_ENGINE_ID` env var to Cloud Run

## 7. Tests

- [x] 7.1 Add unit tests for `MessageProcessor` with memory_service — verify `add_session_to_memory` is called after process, verify graceful behavior when memory_service is None
- [x] 7.2 Add unit test for `create_agent` with tools parameter — verify PreloadMemoryTool is included when passed
- [x] 7.3 Update lifespan tests (if any) to cover both paths: with and without AGENT_ENGINE_ID — skipped, no lifespan tests exist
