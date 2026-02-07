"""ADK Agent factory for the master agent."""

import logging
import os

from google.adk.agents import Agent

logger = logging.getLogger(__name__)

DEFAULT_MODEL = "gemini-2.0-flash"
AGENT_NAME = "master_agent"

DEFAULT_INSTRUCTION = """You are a helpful AI assistant.
You engage in natural conversations and help users with their questions.
Be concise, friendly, and helpful in your responses."""


def load_prompt_from_vertex_ai(project_id: str, location: str, prompt_id: str) -> str | None:
    """Load system prompt from Vertex AI Prompt Management.

    Uses REST API directly to bypass SDK thinkingConfig parsing bug.
    See: https://github.com/googleapis/google-cloud-python/issues/14941

    Args:
        project_id: GCP project ID.
        location: GCP location (e.g., europe-west4).
        prompt_id: Vertex AI Prompt resource ID.

    Returns:
        System instruction text or None if loading fails.
    """
    try:
        import google.auth
        import google.auth.transport.requests
        import httpx

        # Get credentials
        credentials, _ = google.auth.default()
        auth_req = google.auth.transport.requests.Request()
        credentials.refresh(auth_req)

        # Prompts are stored as datasets in Vertex AI
        url = (
            f"https://{location}-aiplatform.googleapis.com/v1beta1/"
            f"projects/{project_id}/locations/{location}/datasets/{prompt_id}"
        )

        headers = {
            "Authorization": f"Bearer {credentials.token}",
            "Content-Type": "application/json",
        }

        response = httpx.get(url, headers=headers, timeout=30)
        response.raise_for_status()
        data = response.json()

        # Extract system instruction from:
        # metadata.promptApiSchema.multimodalPrompt.promptMessage.systemInstruction.parts[0].text
        try:
            system_instruction = (
                data.get("metadata", {})
                .get("promptApiSchema", {})
                .get("multimodalPrompt", {})
                .get("promptMessage", {})
                .get("systemInstruction", {})
                .get("parts", [{}])[0]
                .get("text")
            )

            if system_instruction:
                logger.info(
                    "Loaded prompt from Vertex AI: prompt_id=%s, length=%d",
                    prompt_id,
                    len(system_instruction),
                )
                return system_instruction

        except (IndexError, KeyError, TypeError):
            pass

        logger.warning("Prompt %s has no system instruction", prompt_id)
        return None

    except Exception as e:
        logger.warning(
            "Failed to load prompt from Vertex AI: prompt_id=%s, error=%s",
            prompt_id,
            str(e),
        )
        return None


def create_agent(
    model_name: str | None = None,
    instruction: str | None = None,
) -> Agent:
    """Create and configure an ADK Agent.

    Args:
        model_name: The model to use. Defaults to MODEL_NAME env var or gemini-2.0-flash.
        instruction: Custom instruction for the agent. Defaults to built-in instruction.

    Returns:
        Configured ADK Agent instance.
    """
    if model_name is None:
        model_name = os.environ.get("MODEL_NAME", DEFAULT_MODEL)

    if instruction is None:
        instruction = os.environ.get("AGENT_INSTRUCTION", DEFAULT_INSTRUCTION)

    return Agent(
        name=AGENT_NAME,
        model=model_name,
        instruction=instruction,
        description="Master agent for handling user conversations",
    )
