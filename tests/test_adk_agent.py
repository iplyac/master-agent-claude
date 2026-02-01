"""Tests for ADK Agent factory."""

import os
import pytest
from unittest.mock import patch


class TestCreateAgent:
    """Tests for create_agent function."""

    def test_create_agent_defaults(self):
        """Test agent creation with default values."""
        # Import here to avoid issues with mocks
        from agent.adk_agent import create_agent, AGENT_NAME, DEFAULT_MODEL

        with patch.dict(os.environ, {}, clear=True):
            agent = create_agent()

        assert agent.name == AGENT_NAME
        assert agent.model == DEFAULT_MODEL
        assert agent.instruction is not None

    def test_create_agent_custom_model(self):
        """Test agent creation with custom model."""
        from agent.adk_agent import create_agent

        agent = create_agent(model_name="gemini-1.5-pro")

        assert agent.model == "gemini-1.5-pro"

    def test_create_agent_from_env(self):
        """Test agent creation reads from environment."""
        from agent.adk_agent import create_agent

        with patch.dict(
            os.environ,
            {
                "MODEL_NAME": "gemini-custom",
                "AGENT_INSTRUCTION": "Custom instruction",
            },
        ):
            agent = create_agent()

        assert agent.model == "gemini-custom"
        assert agent.instruction == "Custom instruction"

    def test_create_agent_custom_instruction(self):
        """Test agent creation with custom instruction."""
        from agent.adk_agent import create_agent

        custom_instruction = "You are a specialized assistant."
        agent = create_agent(instruction=custom_instruction)

        assert agent.instruction == custom_instruction

    def test_agent_name_is_master_agent(self):
        """Test agent name is always master-agent."""
        from agent.adk_agent import create_agent, AGENT_NAME

        agent = create_agent()

        assert agent.name == AGENT_NAME
        assert agent.name == "master_agent"

    def test_agent_has_description(self):
        """Test agent has a description."""
        from agent.adk_agent import create_agent

        agent = create_agent()

        assert agent.description is not None
        assert len(agent.description) > 0
