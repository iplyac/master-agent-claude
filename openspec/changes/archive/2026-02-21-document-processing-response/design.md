## Context

The docling agent already returns all the data needed: `content` (full markdown text), `metadata` (pages, tables_found, images_found, processing_time_ms), and `result_gcs_uri`. The master-agent currently passes `content`, `metadata`, and the input `gcs_uri` to the telegram bot. The telegram bot then replies with only a plain text message.

Two gaps exist:
1. `result_gcs_uri` (the output markdown GCS path) is discarded by master-agent and never reaches the bot
2. The bot doesn't use `metadata` for formatting, and doesn't send the markdown as a file

## Goals / Non-Goals

**Goals:**
- Surface processing metadata to the user as a formatted Telegram message
- Deliver extracted content as a `.md` file attachment
- Pass `result_gcs_uri` through master-agent's API response

**Non-Goals:**
- Downloading the MD from GCS in the bot (the `content` field already contains the full text)
- Sending the MD to the agent for further conversation context
- Changing the docling agent or GCS storage logic

## Decisions

**Decision: build the `.md` file from `content`, not from GCS**

The master-agent response already contains the full markdown text in `content`. The bot can create an in-memory `BytesIO` buffer and send it as a Telegram document with `send_document()`. This avoids any GCS credentials or network round-trip in the bot.

Alternative considered: download from `result_gcs_uri` via a new master-agent endpoint. Rejected — unnecessary complexity; `content` already has everything needed.

**Decision: send two separate Telegram messages**

Message 1: formatted processing summary (text).
Message 2: the `.md` file as a document attachment.

Alternative considered: single message with caption + document. Rejected — Telegram captions have a 1024-char limit which is too short for metadata + any preamble.

**Decision: add `result_gcs_uri` to `DocumentResponse` as optional**

The docling agent may not always return `result_gcs_uri` (e.g., if output storage is disabled). Making it `Optional[str]` keeps backward compatibility.

## Risks / Trade-offs

- [Risk] Large markdown content → large Telegram file upload → slow UX → Mitigation: Telegram document upload is async and non-blocking; no size limit concern for typical documents
- [Risk] `metadata` fields missing from docling response → Mitigation: use `.get()` with safe defaults, show "N/A" for missing values
- [Risk] `processing_time_ms` may be 0 or missing for fast documents → Mitigation: display only if present

## Migration Plan

1. Deploy master-agent with updated `DocumentResponse` model (additive, no breaking change)
2. Deploy telegram-bot with updated document handler
3. No rollback risk — both changes are additive; old bot works with new master-agent and vice versa
