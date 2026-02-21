## Context

The master-agent already has `MediaClient` with a live `genai.Client` connected to Vertex AI. It's used for audio transcription and image description. Adding document summarization follows the same pattern: pass content as text, get a text response.

The summary should be generated after docling succeeds, before returning the response to the caller. The content (markdown) can be large — prompting Gemini with the full text is acceptable for typical documents (up to ~100k tokens), but very large content should be truncated to avoid exceeding context limits.

## Goals / Non-Goals

**Goals:**
- Add `summarize_document(content)` to `MediaClient`, returning 2-4 sentence plain-text summary
- Include `summary` in `DocumentResponse` (optional, null if generation fails)
- Show summary in Telegram bot message between metadata stats and file attachment

**Non-Goals:**
- Streaming the summary
- Caching summaries
- Letting the user customise the summary prompt
- Retrying on Gemini failure (non-blocking — proceed without summary)

## Decisions

**Decision: add `summarize_document()` to `MediaClient`, not a separate client**

`MediaClient` already owns the `genai.Client` instance and the pattern for direct Gemini calls. Reusing it avoids creating a second client and keeps all LLM-direct calls in one place.

**Decision: truncate content at 30 000 characters before sending to Gemini**

Typical extracted documents are well under this limit. Truncating prevents hitting context window limits on very large PDFs without adding complex chunking logic.

**Decision: summarization failure is non-blocking**

If Gemini fails (quota, network, model error), the document response is still returned without `summary`. A warning is logged. The user still gets the metadata stats and the file.

**Decision: use the main `model_name` (same as chat), not the image model**

The summary is a pure text task. No reason to use the image-specific model or a separate endpoint.

## Risks / Trade-offs

- [Risk] Extra Gemini call adds latency (~1-3s) to every document request → Mitigation: acceptable for document processing which already takes seconds; can make async in future if needed
- [Risk] Very long documents get truncated → Mitigation: 30k chars covers ~20-30 pages of dense text; sufficient for a summary
- [Risk] Gemini quota hit → Mitigation: failure is non-blocking, user still gets file

## Migration Plan

1. Deploy master-agent (additive `summary` field — old telegram-bot ignores it)
2. Deploy telegram-bot (reads `summary` if present)
3. No rollback risk
