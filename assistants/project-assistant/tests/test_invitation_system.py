"""Tests for the simplified invitation system."""

import pathlib
from datetime import datetime
from unittest.mock import AsyncMock, MagicMock, patch

import pytest
from assistant.command_processor import (
    handle_join_command,
)


class MessageType:
    chat = "chat"
    command = "command"
    notice = "notice"


class ParticipantRole:
    user = "user"
    assistant = "assistant"


class TestSimplifiedInvitationSystem:
    """Test the simplified invitation system."""

    @pytest.fixture
    def context(self):
        """Set up a mocked conversation context."""
        context = AsyncMock()

        # Mock conversation with metadata
        conversation = MagicMock()
        conversation.metadata = {}
        conversation.id = "test-conversation-id"
        context.get_conversation.return_value = conversation
        context.id = "test-conversation-id"

        # Mock send_messages method
        context.send_messages = AsyncMock()

        # Mock send_conversation_state_event method
        context.send_conversation_state_event = AsyncMock()

        # Mock get_participants method
        participants = MagicMock()
        participant = MagicMock()
        participant.id = "test-user-id"
        participant.name = "Test User"
        participant.role = "user"
        participants.participants = [participant]

        context.get_participants.return_value = participants

        # Add assistant property
        context.assistant = MagicMock()
        context.assistant.id = "test-assistant-id"
        context.assistant.name = "Test Assistant"

        # Handle storage directory issues by mocking the storage path functions
        with patch(
            "semantic_workbench_assistant.assistant_app.context.storage_directory_for_context"
        ) as mock_storage_dir:
            mock_storage_dir.return_value = pathlib.Path("/tmp/test-storage")

            # Mock read_model to return None by default
            with patch("semantic_workbench_assistant.storage.read_model") as mock_read_model:
                mock_read_model.return_value = None

                # Also patch write_model from project_storage
                with patch("semantic_workbench_assistant.storage.write_model"):
                    # We'll have this fixture yield in a with-context so the patches remain active
                    yield context

    @pytest.fixture
    def coordinator_command_message(self):
        """Create a start command message fixture."""
        message = MagicMock()
        message.id = "test-command-id"
        message.conversation_id = "test-conversation-id"
        message.created_at = datetime.now()
        message.timestamp = datetime.now()
        message.content = "/start Test Project|This is a test project"
        message.message_type = MessageType.command
        message.command_name = "start"
        message.command_args = "Test Project|This is a test project"

        sender = MagicMock()
        sender.participant_id = "test-user-id"
        sender.participant_role = ParticipantRole.user
        message.sender = sender

        return message

    @pytest.fixture
    def join_command_message(self):
        """Create a join command message fixture."""
        message = MagicMock()
        message.id = "test-command-id"
        message.conversation_id = "test-conversation-id"
        message.created_at = datetime.now()
        message.timestamp = datetime.now()
        message.content = "/join test-project-id"
        message.message_type = MessageType.command
        message.command_name = "join"
        message.command_args = "test-project-id"

        sender = MagicMock()
        sender.participant_id = "test-user-id"
        sender.participant_role = ParticipantRole.user
        message.sender = sender

        return message

    @pytest.mark.asyncio
    @pytest.mark.skip(reason="Test needs significant refactoring after removing ProjectInvitation class")
    @patch("assistant.command_processor.ProjectManager")
    @patch("assistant.command_processor.ProjectStorageManager")
    async def test_redeem_invitation_nonexistent_project(
        self, mock_storage_manager, mock_project_manager, context, join_command_message
    ):
        """Test that joining a nonexistent project fails."""
        # This test needs to be refactored after removing ProjectInvitation class
        pass

    @pytest.mark.asyncio
    @patch("assistant.command_processor.ProjectManager")
    @patch("assistant.conversation_clients.ProjectStorageManager")
    async def test_join_nonexistent_project(
        self, mock_storage_manager, mock_project_manager, context, join_command_message
    ):
        """Test that join command fails with clear message for nonexistent project ID."""
        # Setup project existence check to fail
        mock_storage_manager.project_exists.return_value = False

        # Make ProjectManager.get_project_id return an awaitable mock
        get_project_id_mock = AsyncMock()
        get_project_id_mock.return_value = None
        mock_project_manager.get_project_id = get_project_id_mock

        # Setup project join operation to fail
        with patch("assistant.command_processor.ProjectManager.join_project") as mock_join:
            mock_join.return_value = False

            # Reset the send_messages mock
            context.send_messages.reset_mock()

            # Call the handler directly
            with patch("assistant.command_processor.ProjectStorageManager", mock_storage_manager):
                await handle_join_command(context, join_command_message, ["nonexistent-project-id"])

                # Check that an error message was sent
                context.send_messages.assert_called_once()

                # Verify the message contains error about invalid or nonexistent project
                args, kwargs = context.send_messages.call_args
                message_content = args[0].content
                assert (
                    "invalid" in message_content.lower()
                    or "not found" in message_content.lower()
                    or "does not exist" in message_content.lower()
                )
