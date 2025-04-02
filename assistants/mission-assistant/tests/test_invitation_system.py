"""Tests for the simplified invitation system."""

from datetime import datetime
import pathlib
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from assistant.command_processor import (
    handle_join_command,
    handle_start_hq_command,
)
from assistant.mission import MissionInvitation


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
        with patch("assistant.mission_storage.storage_directory_for_context") as mock_storage_dir:
            mock_storage_dir.return_value = pathlib.Path("/tmp/test-storage")
            
            # Mock read_model to return None by default
            with patch("assistant.mission_storage.read_model") as mock_read_model:
                mock_read_model.return_value = None
                
                # Also patch write_model
                with patch("assistant.mission_storage.write_model"):
                    # We'll have this fixture yield in a with-context so the patches remain active
                    yield context
    
    @pytest.fixture
    def hq_command_message(self):
        """Create a start-hq command message fixture."""
        message = MagicMock()
        message.id = "test-command-id"
        message.conversation_id = "test-conversation-id"
        message.created_at = datetime.now()
        message.timestamp = datetime.now()
        message.content = "/start-hq Test Mission|This is a test mission"
        message.message_type = MessageType.command
        message.command_name = "start-hq"
        message.command_args = "Test Mission|This is a test mission"
        
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
        message.content = "/join test-mission-id"
        message.message_type = MessageType.command
        message.command_name = "join"
        message.command_args = "test-mission-id"
        
        sender = MagicMock()
        sender.participant_id = "test-user-id"
        sender.participant_role = ParticipantRole.user
        message.sender = sender
        
        return message

    @pytest.mark.asyncio
    @patch("assistant.command_processor.ConversationMissionManager")
    @patch("assistant.command_processor.MissionManager")
    @patch("assistant.command_processor.MissionStorageManager")
    @patch("assistant.mission_storage.generate_id")
    async def test_start_hq_displays_mission_id(self, mock_generate_id, mock_storage_manager, mock_mission_manager, mock_conv_manager, context, hq_command_message):
        """Test that start-hq displays mission ID as invitation code."""
        # Mock generate_id to return predictable ID
        mock_generate_id.return_value = "test-mission-id"
        
        # Reset the send_messages mock
        context.send_messages.reset_mock()
        
        # Call the handler directly
        await handle_start_hq_command(context, hq_command_message, ["Test Mission|This is a test mission"])
        
        # Check that a message was sent
        context.send_messages.assert_called_once()
        
        # Verify the message contains the mission ID as invitation code
        args, kwargs = context.send_messages.call_args
        message_content = args[0].content
        assert "test-mission-id" in message_content
        assert "Share this Mission ID" in message_content

    @pytest.mark.asyncio
    @patch("assistant.command_processor.ConversationMissionManager")
    @patch("assistant.command_processor.MissionManager")
    @patch("assistant.mission.MissionStorageManager")
    async def test_join_uses_mission_id_directly(self, mock_storage_manager, mock_mission_manager, mock_conv_manager, context, join_command_message):
        """Test that join command uses mission ID directly."""
        # Setup mission existence check
        mock_storage_manager.mission_exists.return_value = True
        
        # Set up mission invitation redemption to succeed
        with patch("assistant.mission.MissionInvitation.redeem_invitation") as mock_redeem:
            mock_redeem.return_value = True
            
            # Reset the send_messages mock
            context.send_messages.reset_mock()
            
            # Call the handler directly
            await handle_join_command(context, join_command_message, ["test-mission-id"])
            
            # Check that a success message was sent
            context.send_messages.assert_called_once()
            
            # Verify the message contains success confirmation
            args, kwargs = context.send_messages.call_args
            message_content = args[0].content
            assert "successfully joined" in message_content.lower() or "joined successfully" in message_content.lower()

    @pytest.mark.asyncio
    @patch("assistant.mission_storage.MissionStorageManager")
    async def test_redeem_invitation_with_mission_id(self, mock_storage_manager, context):
        """Test that redeem_invitation uses mission ID directly."""
        # Setup mission existence check
        mock_storage_manager.mission_exists.return_value = True
        
        # Call redeem_invitation directly
        result, message = await MissionInvitation.redeem_invitation(context, "test-mission-id")
        
        # Check result indicates success
        assert result is True
        
        # Verify that mission_exists was called with the mission ID
        mock_storage_manager.mission_exists.assert_called_once_with("test-mission-id")

    @pytest.mark.asyncio
    @patch("assistant.mission_storage.MissionStorageManager")
    async def test_redeem_invitation_nonexistent_mission(self, mock_storage_manager, context):
        """Test that redeem_invitation fails with nonexistent mission ID."""
        # Setup mission existence check to fail
        mock_storage_manager.mission_exists.return_value = False
        
        # Call redeem_invitation directly
        result, message = await MissionInvitation.redeem_invitation(context, "nonexistent-mission-id")
        
        # Check result indicates failure
        assert result is False
        
        # Verify that mission_exists was called with the mission ID
        mock_storage_manager.mission_exists.assert_called_once_with("nonexistent-mission-id")

    @pytest.mark.asyncio
    @patch("assistant.mission_storage.MissionStorageManager")
    async def test_join_nonexistent_mission(self, mock_storage_manager, context, join_command_message):
        """Test that join command fails with clear message for nonexistent mission ID."""
        # Setup mission existence check to fail
        mock_storage_manager.mission_exists.return_value = False
        
        # Setup mission invitation redemption to fail
        with patch("assistant.mission.MissionInvitation.redeem_invitation") as mock_redeem:
            mock_redeem.return_value = False
            
            # Reset the send_messages mock
            context.send_messages.reset_mock()
            
            # Call the handler directly
            with patch("assistant.command_processor.MissionStorageManager", mock_storage_manager):
                await handle_join_command(context, join_command_message, ["nonexistent-mission-id"])
                
                # Check that an error message was sent
                context.send_messages.assert_called_once()
                
                # Verify the message contains error about invalid or nonexistent mission
                args, kwargs = context.send_messages.call_args
                message_content = args[0].content
                assert "invalid" in message_content.lower() or "not found" in message_content.lower() or "does not exist" in message_content.lower()
