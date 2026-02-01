## 1. Dependencies

- [x] 1.1 Add `google-adk` to requirements.txt
- [x] 1.2 Remove `google-generativeai` from requirements.txt
- [x] 1.3 Run `pip install -r requirements.txt` to verify dependencies resolve

## 2. FirestoreSessionService

- [x] 2.1 Create `agent/adk_session_service.py` with FirestoreSessionService class
- [x] 2.2 Implement `__init__` with Firestore client initialization
- [x] 2.3 Implement `create_session` method (create or return existing)
- [x] 2.4 Implement `get_session` method (retrieve from Firestore)
- [x] 2.5 Implement `list_sessions` method
- [x] 2.6 Implement `delete_session` method
- [x] 2.7 Implement event persistence with 100 event limit
- [x] 2.8 Add unit tests for FirestoreSessionService in `tests/test_adk_session_service.py`

## 3. ADK Agent

- [x] 3.1 Create `agent/adk_agent.py` with agent factory function
- [x] 3.2 Configure Agent with model from MODEL_NAME env var (default: gemini-2.0-flash)
- [x] 3.3 Configure Agent name as "master-agent"
- [x] 3.4 Add agent instruction configuration
- [x] 3.5 Add unit tests for agent creation in `tests/test_adk_agent.py`

## 4. Processor Refactoring

- [x] 4.1 Update `agent/processor.py` to use ADK Runner instead of LLMClient
- [x] 4.2 Implement message processing with `runner.run_async()`
- [x] 4.3 Handle event stream and extract final response via `is_final_response()`
- [x] 4.4 Map conversation_id to session_id and user_id
- [x] 4.5 Add error handling for Runner exceptions
- [x] 4.6 Keep voice processing with direct Gemini API call (temporary)
- [x] 4.7 Update tests in `tests/test_chat_api.py` for new processor

## 5. Application Integration

- [x] 5.1 Update `app.py` lifespan to create ADK Agent
- [x] 5.2 Update `app.py` lifespan to create FirestoreSessionService
- [x] 5.3 Update `app.py` lifespan to create Runner and store in app.state
- [x] 5.4 Update `/api/chat` endpoint to use new processor
- [x] 5.5 Keep `/api/voice` endpoint working with existing voice processing
- [x] 5.6 Remove LLMClient from lifespan (except voice-related parts)

## 6. Cleanup

- [x] 6.1 Remove or refactor `agent/llm_client.py` (keep voice methods only)
- [x] 6.2 Remove `agent/conversation_store.py` (replaced by ADK SessionService)
- [x] 6.3 Update imports across codebase
- [x] 6.4 Remove obsolete tests

## 7. Verification

- [x] 7.1 Run all unit tests
- [x] 7.2 Test locally with curl: `/api/chat` endpoint
- [x] 7.3 Verify conversation context persists between messages
- [x] 7.4 Test `/api/voice` endpoint still works
- [ ] 7.5 Deploy to staging and verify with Telegram bot
