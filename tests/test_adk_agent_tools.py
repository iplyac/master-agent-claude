"""Tests for create_agent with tools parameter."""

import pytest
from unittest.mock import MagicMock


def test_create_agent_without_tools():
    """create_agent without tools should create agent with no tools."""
    from agent.adk_agent import create_agent

    agent = create_agent(model_name="gemini-2.0-flash")
    # Agent should not have tools attribute or it should be empty/None
    assert not getattr(agent, "tools", None)


def test_create_agent_with_tools():
    """create_agent with tools should pass them to Agent."""
    from agent.adk_agent import create_agent

    mock_tool = MagicMock()
    mock_tool.name = "test_tool"
    agent = create_agent(model_name="gemini-2.0-flash", tools=[mock_tool])
    assert agent.tools is not None
    assert mock_tool in agent.tools


def test_create_agent_with_empty_tools():
    """create_agent with empty tools list should not set tools."""
    from agent.adk_agent import create_agent

    agent = create_agent(model_name="gemini-2.0-flash", tools=[])
    # Empty list is falsy, so tools should not be set
    assert not getattr(agent, "tools", None)
