import logging
import os
import sys
from contextlib import asynccontextmanager
from contextvars import ContextVar

from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse
from pythonjsonlogger import jsonlogger

from google.adk.runners import Runner
from google.adk.sessions import InMemorySessionService

from agent.adk_agent import create_agent
from agent.config import (
    get_location,
    get_log_level,
    get_model_name,
    get_port,
    get_project_id,
    get_region,
    get_service_name,
    mask_token,
)
from agent.models import ChatRequest, SessionInfoRequest, SessionInfoResponse, VoiceRequest
from agent.processor import MessageProcessor
from agent.voice_client import VoiceClient

# Cloud Trace context variable
trace_context: ContextVar[str] = ContextVar("trace_context", default="")


class CloudTraceFormatter(jsonlogger.JsonFormatter):
    """JSON formatter that includes Cloud Trace context."""

    def __init__(self, *args, project_id: str = "", **kwargs):
        super().__init__(*args, **kwargs)
        self.project_id = project_id

    def add_fields(self, log_record, record, message_dict):
        super().add_fields(log_record, record, message_dict)
        log_record["timestamp"] = self.formatTime(record)
        log_record["level"] = record.levelname
        log_record["logger"] = record.name

        trace_id = trace_context.get("")
        if trace_id and self.project_id:
            log_record["logging.googleapis.com/trace"] = (
                f"projects/{self.project_id}/traces/{trace_id}"
            )


def setup_logging(project_id: str, log_level: str) -> None:
    """Configure JSON structured logging."""
    handler = logging.StreamHandler(sys.stdout)
    formatter = CloudTraceFormatter(
        "%(timestamp)s %(level)s %(logger)s %(message)s",
        project_id=project_id,
    )
    handler.setFormatter(formatter)

    root_logger = logging.getLogger()
    root_logger.handlers.clear()
    root_logger.addHandler(handler)
    root_logger.setLevel(getattr(logging, log_level, logging.INFO))

    # Suppress noisy third-party loggers
    logging.getLogger("uvicorn.access").setLevel(logging.WARNING)
    logging.getLogger("httpx").setLevel(logging.WARNING)


logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Manage ADK components lifecycle."""
    # --- Startup ---
    project_id = get_project_id()
    log_level = get_log_level()
    setup_logging(project_id, log_level)

    port = get_port()
    model_name = get_model_name()
    region = get_region()
    service_name = get_service_name()

    logger.info(
        "Starting %s: port=%d, model=%s, region=%s, backend=VertexAI",
        service_name,
        port,
        model_name,
        region,
    )

    # Create ADK components
    agent = create_agent(model_name=model_name)

    # Get location for Vertex AI services
    location = get_location()

    # Use InMemorySessionService for now (VertexAiSessionService requires ReasoningEngine deployment)
    # TODO: Implement DatabaseSessionService with Cloud SQL for persistence
    logger.info("Using InMemorySessionService (sessions not persisted across restarts)")
    session_service = InMemorySessionService()

    runner = Runner(
        app_name="master_agent",
        agent=agent,
        session_service=session_service,
    )

    # Create voice client for audio processing (uses Vertex AI)
    voice_client = VoiceClient(project_id, location, model_name)

    # Create processor with ADK Runner
    processor = MessageProcessor(runner, session_service, voice_client)

    # Store in app state
    app.state.runner = runner
    app.state.session_service = session_service
    app.state.processor = processor
    app.state.voice_client = voice_client

    yield

    # --- Shutdown ---
    logger.info("Shutting down %s", service_name)
    await voice_client.close()
    if hasattr(session_service, "close"):
        await session_service.close()


app = FastAPI(lifespan=lifespan)


@app.middleware("http")
async def trace_middleware(request: Request, call_next):
    """Extract X-Cloud-Trace-Context header and store in contextvar."""
    trace_header = request.headers.get("X-Cloud-Trace-Context", "")
    if trace_header:
        trace_id = trace_header.split("/")[0]
        trace_context.set(trace_id)
    else:
        trace_context.set("")

    response = await call_next(request)
    return response


@app.get("/health")
async def health():
    return {"status": "ok"}


@app.get("/healthz")
async def healthz():
    return {"status": "ok"}


@app.post("/api/session-info")
async def session_info(request: Request):
    """Get session information by conversation_id."""
    try:
        body = await request.json()
    except Exception:
        return JSONResponse(
            status_code=400,
            content={"error": "Invalid JSON"},
        )

    try:
        info_request = SessionInfoRequest(**body)
    except ValueError as e:
        return JSONResponse(
            status_code=400,
            content={"error": str(e)},
        )

    conversation_id = info_request.conversation_id
    session_service = request.app.state.session_service

    # Check if session exists
    try:
        session = await session_service.get_session(
            app_name="master_agent",
            user_id=conversation_id,
            session_id=conversation_id,
        )
        session_exists = session is not None
        message_count = len(session.events) if session and hasattr(session, "events") else None
    except Exception:
        session_exists = False
        message_count = None

    response = SessionInfoResponse(
        conversation_id=conversation_id,
        session_id=conversation_id,
        session_exists=session_exists,
        message_count=message_count,
    )
    return response.model_dump()


@app.post("/api/chat")
async def chat(request: Request):
    try:
        body = await request.json()
    except Exception:
        return JSONResponse(
            status_code=400,
            content={"error": "Invalid JSON"},
        )

    try:
        chat_request = ChatRequest(**body)
    except ValueError as e:
        return JSONResponse(
            status_code=400,
            content={"error": str(e)},
        )

    conversation_id = chat_request.get_conversation_id()
    message = chat_request.message

    if not message:
        return JSONResponse(
            status_code=400,
            content={"error": "message is required"},
        )

    # Log telegram metadata if present
    if chat_request.metadata and chat_request.metadata.telegram:
        tg = chat_request.metadata.telegram
        logger.info(
            "Chat request with Telegram metadata: conversation_id=%s, chat_id=%d, user_id=%d, chat_type=%s",
            conversation_id,
            tg.chat_id,
            tg.user_id,
            tg.chat_type,
        )

    try:
        processor: MessageProcessor = request.app.state.processor
        response_text = await processor.process(conversation_id, message)
        return {"response": response_text}
    except Exception as e:
        error_msg = mask_token(str(e))
        logger.error("Chat error: conversation_id=%s, error=%s", conversation_id, error_msg)
        return JSONResponse(
            status_code=500,
            content={"error": "Agent unavailable, please try again later"},
        )


@app.post("/api/voice")
async def voice(request: Request):
    """
    Process voice message via Gemini multimodal API.

    Request JSON:
    {
        "conversation_id": "tg_<chat_id>",
        "audio_base64": "<base64-encoded-audio>",
        "mime_type": "audio/ogg",
        "metadata": {"telegram": {"chat_id": 123, "user_id": 456, "chat_type": "private"}}
    }

    Response JSON:
    {
        "response": "<agent_reply>",
        "transcription": "<transcribed_text>"
    }
    """
    try:
        body = await request.json()
    except Exception:
        return JSONResponse(status_code=400, content={"error": "Invalid JSON"})

    try:
        voice_request = VoiceRequest(**body)
    except ValueError as e:
        return JSONResponse(
            status_code=400,
            content={"error": str(e)},
        )

    conversation_id = voice_request.get_conversation_id()
    audio_base64 = voice_request.audio_base64
    mime_type = voice_request.mime_type

    if not audio_base64:
        return JSONResponse(
            status_code=400,
            content={"error": "audio_base64 is required"},
        )

    # Log request (without audio content)
    audio_size = len(audio_base64) * 3 // 4
    logger.info(
        "Voice API request: conversation_id=%s, audio_size=%d, mime_type=%s",
        conversation_id,
        audio_size,
        mime_type,
    )

    # Log telegram metadata if present
    if voice_request.metadata and voice_request.metadata.telegram:
        tg = voice_request.metadata.telegram
        logger.info(
            "Voice request with Telegram metadata: conversation_id=%s, chat_id=%d, user_id=%d, chat_type=%s",
            conversation_id,
            tg.chat_id,
            tg.user_id,
            tg.chat_type,
        )

    try:
        processor: MessageProcessor = request.app.state.processor
        result = await processor.process_voice(conversation_id, audio_base64, mime_type)
        return result
    except Exception as e:
        error_msg = mask_token(str(e))
        logger.error("Voice API error: conversation_id=%s, error=%s", conversation_id, error_msg)
        return JSONResponse(
            status_code=500,
            content={"error": "Agent unavailable, please try again later"},
        )


if __name__ == "__main__":
    import uvicorn

    uvicorn.run(
        "app:app",
        host="0.0.0.0",
        port=get_port(),
        timeout_graceful_shutdown=9,
    )
