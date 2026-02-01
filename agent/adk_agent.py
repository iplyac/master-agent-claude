"""ADK Agent factory for the master agent."""

import os
from google.adk.agents import Agent

DEFAULT_MODEL = "gemini-2.0-flash"
AGENT_NAME = "master_agent"

DEFAULT_INSTRUCTION = """You are a helpful AI assistant.
You engage in natural conversations and help users with their questions.
Be concise, friendly, and helpful in your responses."""


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
