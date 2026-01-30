import logging
import sys
from contextlib import asynccontextmanager
from contextvars import ContextVar

from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse
from pythonjsonlogger import jsonlogger

from agent.config import (
    get_log_level,
    get_model_api_key,
    get_model_endpoint,
    get_model_name,
    get_port,
    get_project_id,
    get_region,
    get_service_name,
    mask_token,
)
from agent.llm_client import LLMClient
from agent.processor import MessageProcessor

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
    """Manage LLM client lifecycle."""
    # --- Startup ---
    project_id = get_project_id()
    log_level = get_log_level()
    setup_logging(project_id, log_level)

    port = get_port()
    api_key = get_model_api_key()
    model_name = get_model_name()
    endpoint = get_model_endpoint()
    region = get_region()
    service_name = get_service_name()

    logger.info(
        "Starting %s: port=%d, model=%s, region=%s, api_key_configured=%s",
        service_name,
        port,
        model_name,
        region,
        api_key is not None,
    )

    llm_client = LLMClient(api_key, model_name, endpoint)
    processor = MessageProcessor(llm_client)

    app.state.llm_client = llm_client
    app.state.processor = processor

    yield

    # --- Shutdown ---
    logger.info("Shutting down %s", service_name)
    await llm_client.close()


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


@app.post("/api/chat")
async def chat(request: Request):
    try:
        body = await request.json()
    except Exception:
        return JSONResponse(
            status_code=400,
            content={"error": "Invalid JSON"},
        )

    session_id = body.get("session_id", "")
    message = body.get("message", "")

    if not session_id or not message:
        return JSONResponse(
            status_code=400,
            content={"error": "session_id and message are required"},
        )

    try:
        processor: MessageProcessor = request.app.state.processor
        response_text = await processor.process(session_id, message)
        return {"response": response_text}
    except Exception as e:
        error_msg = mask_token(str(e))
        logger.error("Chat error: session_id=%s, error=%s", session_id, error_msg)
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
        "session_id": "tg_<user_id>",
        "audio_base64": "<base64-encoded-audio>",
        "mime_type": "audio/ogg"
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

    session_id = body.get("session_id", "")
    audio_base64 = body.get("audio_base64", "")
    mime_type = body.get("mime_type", "audio/ogg")

    if not session_id or not audio_base64:
        return JSONResponse(
            status_code=400,
            content={"error": "session_id and audio_base64 are required"},
        )

    # Log request (without audio content)
    audio_size = len(audio_base64) * 3 // 4
    logger.info(
        "Voice API request: session_id=%s, audio_size=%d, mime_type=%s",
        session_id,
        audio_size,
        mime_type,
    )

    try:
        processor: MessageProcessor = request.app.state.processor
        result = await processor.process_voice(session_id, audio_base64, mime_type)
        return result
    except Exception as e:
        error_msg = mask_token(str(e))
        logger.error("Voice API error: session_id=%s, error=%s", session_id, error_msg)
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
