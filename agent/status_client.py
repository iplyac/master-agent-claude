"""Async client for collecting status from all known agents."""

import asyncio
import logging
from datetime import datetime, timezone

import httpx

logger = logging.getLogger(__name__)

_TIMEOUT = 5.0
_UNREACHABLE: dict = {"status": "unreachable", "version": "unknown", "uptime_seconds": None}


async def _fetch_status(client: httpx.AsyncClient, url: str, name: str, purpose: str) -> dict:
    try:
        resp = await client.get(f"{url}/status", timeout=_TIMEOUT)
        resp.raise_for_status()
        data = resp.json()
        return {
            "name": name,
            "purpose": data.get("purpose", purpose),
            "version": data.get("version", "unknown"),
            "uptime_seconds": data.get("uptime_seconds"),
            "status": "ok",
        }
    except Exception as e:
        logger.warning("Failed to fetch status from %s: %s", name, e)
        return {"name": name, "purpose": purpose, **_UNREACHABLE}


async def collect_agents_status(
    *,
    telegram_bot_url: str | None,
    docling_agent_url: str | None,
    self_version: str,
    self_started_at: datetime,
) -> list[dict]:
    """Collect status from all known agents and return ordered list."""
    self_uptime = (datetime.now(timezone.utc) - self_started_at).total_seconds()
    self_entry = {
        "name": "master-agent",
        "purpose": "AI orchestrator — processes messages via Google ADK/Gemini, coordinates sub-agents",
        "version": self_version,
        "uptime_seconds": self_uptime,
        "status": "ok",
    }

    bot_purpose = "Telegram interface — forwards user messages to master-agent and returns responses"
    docling_purpose = "Document processor — converts PDF/DOCX/PPTX/HTML to structured text using Docling"

    tasks = []
    labels = []

    async with httpx.AsyncClient() as client:
        if telegram_bot_url:
            tasks.append(_fetch_status(client, telegram_bot_url, "telegram-bot", bot_purpose))
            labels.append("telegram-bot")
        if docling_agent_url:
            tasks.append(_fetch_status(client, docling_agent_url, "docling-agent", docling_purpose))
            labels.append("docling-agent")

        results = await asyncio.gather(*tasks, return_exceptions=True)

    fetched: dict[str, dict] = {}
    for label, result in zip(labels, results):
        if isinstance(result, Exception):
            fetched[label] = {"name": label, "purpose": "", **_UNREACHABLE}
        else:
            fetched[label] = result  # type: ignore[assignment]

    # Fixed order: [telegram-bot, master-agent, docling-agent]
    bot_entry = fetched.get(
        "telegram-bot",
        {"name": "telegram-bot", "purpose": bot_purpose, **_UNREACHABLE},
    )
    docling_entry = fetched.get(
        "docling-agent",
        {"name": "docling-agent", "purpose": docling_purpose, **_UNREACHABLE},
    )

    return [bot_entry, self_entry, docling_entry]
