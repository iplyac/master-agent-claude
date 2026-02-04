# Telegram Bot Integration

## Session Info Endpoint

The `/api/session-info` endpoint allows you to query session information by conversation ID.

### Request

```http
POST /api/session-info
Content-Type: application/json

{
  "conversation_id": "tg_dm_234759359"
}
```

### Response

**Success (200):**
```json
{
  "conversation_id": "tg_dm_234759359",
  "session_id": "tg_dm_234759359",
  "session_exists": true,
  "message_count": 5
}
```

**Non-existing session (200):**
```json
{
  "conversation_id": "tg_dm_234759359",
  "session_id": "tg_dm_234759359",
  "session_exists": false,
  "message_count": null
}
```

**Missing conversation_id (400):**
```json
{
  "error": "1 validation error for SessionInfoRequest\nconversation_id\n  Field required..."
}
```

### Fields

| Field | Type | Description |
|-------|------|-------------|
| `conversation_id` | string | The conversation identifier (same as input) |
| `session_id` | string | The session identifier used by ADK (currently same as conversation_id) |
| `session_exists` | boolean | Whether the session exists in session storage |
| `message_count` | int \| null | Number of events in session (null if session doesn't exist or not supported) |

## Adding /sessioninfo Command to Telegram Bot

Add this handler to your telegram-bot to support the `/sessioninfo` command:

```python
import httpx
from telegram import Update
from telegram.ext import ContextTypes, CommandHandler

MASTER_AGENT_URL = "https://your-master-agent-url.run.app"


async def sessioninfo_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Handle /sessioninfo command - show current session info."""
    chat_id = update.effective_chat.id
    chat_type = update.effective_chat.type

    # Build conversation_id using same format as chat messages
    if chat_type == "private":
        conversation_id = f"tg_dm_{chat_id}"
    else:
        conversation_id = f"tg_group_{chat_id}"

    async with httpx.AsyncClient() as client:
        try:
            response = await client.post(
                f"{MASTER_AGENT_URL}/api/session-info",
                json={"conversation_id": conversation_id},
                timeout=10.0,
            )
            response.raise_for_status()
            data = response.json()

            if data.get("session_exists"):
                message_count = data.get("message_count")
                count_str = f"\nMessages: {message_count}" if message_count is not None else ""
                text = f"Session info:\n- Conversation ID: `{data['conversation_id']}`\n- Session ID: `{data['session_id']}`\n- Status: Active{count_str}"
            else:
                text = f"No active session for this chat.\n- Conversation ID: `{conversation_id}`"

        except httpx.HTTPError as e:
            text = f"Failed to get session info: {e}"

    await update.message.reply_text(text, parse_mode="Markdown")


# Register the handler in your application setup:
# application.add_handler(CommandHandler("sessioninfo", sessioninfo_command))
```

### Notes

- The `conversation_id` format matches what telegram-bot already uses for chat/voice messages
- Sessions are stored in memory and do not persist across master-agent restarts
- The `message_count` reflects ADK events, not individual user messages

## Image Endpoint

The `/api/image` endpoint allows you to send images for recognition and processing.

### Request

```http
POST /api/image
Content-Type: application/json

{
  "conversation_id": "tg_dm_234759359",
  "image_base64": "<base64-encoded-image>",
  "mime_type": "image/jpeg",
  "prompt": "What is in this image?",
  "metadata": {
    "telegram": {
      "chat_id": 234759359,
      "user_id": 123456,
      "chat_type": "private"
    }
  }
}
```

### Fields

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `conversation_id` | string | Yes | The conversation identifier |
| `image_base64` | string | Yes | Base64-encoded image data |
| `mime_type` | string | No | Image MIME type (default: `image/jpeg`). Supported: `image/jpeg`, `image/png`, `image/webp`, `image/gif` |
| `prompt` | string | No | Optional question about the image |
| `metadata` | object | No | Optional Telegram metadata |

### Response

**Success (200):**
```json
{
  "response": "This image shows a cat sitting on a windowsill...",
  "description": "A tabby cat with orange and white fur sitting on a wooden windowsill, looking outside through a glass window."
}
```

**Invalid base64 (400):**
```json
{
  "error": "Invalid base64 encoding"
}
```

**Unsupported mime type (400):**
```json
{
  "error": "Unsupported mime_type. Supported: image/jpeg, image/png, image/webp, image/gif"
}
```

## Handling Photo Messages in Telegram Bot

Add this handler to process photo messages:

```python
import base64
import httpx
from telegram import Update
from telegram.ext import ContextTypes, MessageHandler, filters

MASTER_AGENT_URL = "https://your-master-agent-url.run.app"


async def photo_handler(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Handle photo messages - send to master-agent for recognition."""
    chat_id = update.effective_chat.id
    chat_type = update.effective_chat.type
    user_id = update.effective_user.id

    # Build conversation_id
    if chat_type == "private":
        conversation_id = f"tg_dm_{chat_id}"
    else:
        conversation_id = f"tg_group_{chat_id}"

    # Get the largest photo (best quality)
    photo = update.message.photo[-1]
    file = await context.bot.get_file(photo.file_id)

    # Download and encode to base64
    photo_bytes = await file.download_as_bytearray()
    image_base64 = base64.b64encode(photo_bytes).decode("utf-8")

    # Get caption as prompt (if any)
    prompt = update.message.caption

    async with httpx.AsyncClient() as client:
        try:
            response = await client.post(
                f"{MASTER_AGENT_URL}/api/image",
                json={
                    "conversation_id": conversation_id,
                    "image_base64": image_base64,
                    "mime_type": "image/jpeg",
                    "prompt": prompt,
                    "metadata": {
                        "telegram": {
                            "chat_id": chat_id,
                            "user_id": user_id,
                            "chat_type": chat_type,
                        }
                    },
                },
                timeout=60.0,
            )
            response.raise_for_status()
            data = response.json()
            text = data.get("response", "Could not process the image.")
        except httpx.HTTPError as e:
            text = f"Failed to process image: {e}"

    await update.message.reply_text(text)


# Register the handler in your application setup:
# application.add_handler(MessageHandler(filters.PHOTO, photo_handler))
```

### Notes

- Telegram compresses photos before sending, so image quality may vary
- The `prompt` field is optional - if omitted, the agent will describe the image
- Use the photo caption as `prompt` to ask specific questions about the image
- Session context is preserved - the agent remembers previous images in the conversation
