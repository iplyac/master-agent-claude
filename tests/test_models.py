"""Tests for Pydantic request models."""

import pytest
from pydantic import ValidationError

from agent.models import (
    ChatRequest,
    VoiceRequest,
    TelegramMetadata,
    RequestMetadata,
)


class TestChatRequest:
    """Tests for ChatRequest model."""

    def test_new_format_with_conversation_id(self):
        """Test new format with conversation_id."""
        request = ChatRequest(
            conversation_id="tg_dm_12345678",
            message="hello",
            metadata=RequestMetadata(
                telegram=TelegramMetadata(
                    chat_id=12345678,
                    user_id=12345678,
                    chat_type="private",
                )
            ),
        )
        assert request.get_conversation_id() == "tg_dm_12345678"
        assert request.metadata.telegram.chat_id == 12345678

    def test_backward_compat_with_session_id(self):
        """Test backward compatibility with session_id."""
        request = ChatRequest(
            session_id="tg_123",
            message="hello",
        )
        assert request.get_conversation_id() == "tg_123"

    def test_conversation_id_takes_precedence(self):
        """Test that conversation_id takes precedence over session_id."""
        request = ChatRequest(
            conversation_id="new_id",
            session_id="old_id",
            message="hello",
        )
        assert request.get_conversation_id() == "new_id"

    def test_error_when_no_identifier(self):
        """Test error when neither conversation_id nor session_id provided."""
        with pytest.raises(ValidationError) as exc_info:
            ChatRequest(message="hello")
        assert "conversation_id or session_id" in str(exc_info.value).lower()


class TestVoiceRequest:
    """Tests for VoiceRequest model."""

    def test_new_format_with_conversation_id(self):
        """Test new format with conversation_id."""
        request = VoiceRequest(
            conversation_id="tg_dm_12345678",
            audio_base64="SGVsbG8gV29ybGQ=",
            mime_type="audio/ogg",
            metadata=RequestMetadata(
                telegram=TelegramMetadata(
                    chat_id=12345678,
                    user_id=12345678,
                    chat_type="private",
                )
            ),
        )
        assert request.get_conversation_id() == "tg_dm_12345678"

    def test_backward_compat_with_session_id(self):
        """Test backward compatibility with session_id."""
        request = VoiceRequest(
            session_id="tg_123",
            audio_base64="SGVsbG8gV29ybGQ=",
        )
        assert request.get_conversation_id() == "tg_123"

    def test_error_when_no_identifier(self):
        """Test error when neither conversation_id nor session_id provided."""
        with pytest.raises(ValidationError) as exc_info:
            VoiceRequest(audio_base64="SGVsbG8gV29ybGQ=")
        assert "conversation_id or session_id" in str(exc_info.value).lower()


class TestTelegramMetadata:
    """Tests for TelegramMetadata model."""

    def test_valid_metadata(self):
        """Test valid telegram metadata."""
        metadata = TelegramMetadata(
            chat_id=12345678,
            user_id=87654321,
            chat_type="private",
        )
        assert metadata.chat_id == 12345678
        assert metadata.user_id == 87654321
        assert metadata.chat_type == "private"

    def test_group_chat_type(self):
        """Test group chat metadata."""
        metadata = TelegramMetadata(
            chat_id=-100123456789,
            user_id=12345678,
            chat_type="supergroup",
        )
        assert metadata.chat_type == "supergroup"
