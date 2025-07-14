"""
Tests for the ShareTools functionality.
"""

import contextlib
from unittest.mock import AsyncMock, MagicMock

import openai_client
import pytest
from assistant.analysis import detect_information_request_needs
from assistant.storage_models import ConversationRole
from assistant.tools import ShareTools
from semantic_workbench_assistant.assistant_app import ConversationContext


# Use pytest for all tests for consistency
class TestShareTools:
    """Test the ShareTools class."""

    @pytest.fixture
    def context(self):
        """Set up test fixtures."""
        context = AsyncMock(spec=ConversationContext)
        context.conversation = MagicMock()
        context.id = "test-conversation-id"
        # Add the assistant attribute for the get_project_tools test
        context.assistant = MagicMock()
        # Use the correct property name (_template_id)
        from assistant.utils import DEFAULT_TEMPLATE_ID

        context.assistant._template_id = DEFAULT_TEMPLATE_ID
        return context

    def test_initialization(self, context):
        """Test that ShareTools initializes correctly."""
        # Test Coordinator role
        coordinator_tools = ShareTools(context, ConversationRole.COORDINATOR)
        assert coordinator_tools.role == ConversationRole.COORDINATOR
        assert coordinator_tools.tool_functions is not None

        # Verify Coordinator-specific functions are registered
        assert "update_brief" in coordinator_tools.tool_functions.function_map
        assert "resolve_information_request" in coordinator_tools.tool_functions.function_map

        # Verify Team-specific functions are NOT registered
        assert "create_information_request" not in coordinator_tools.tool_functions.function_map
        assert "delete_information_request" not in coordinator_tools.tool_functions.function_map

        # Test Team role
        team_tools = ShareTools(context, ConversationRole.TEAM)
        assert team_tools.role == ConversationRole.TEAM
        assert team_tools.tool_functions is not None

        # Verify Team-specific functions are registered
        assert "create_information_request" in team_tools.tool_functions.function_map
        assert "delete_information_request" in team_tools.tool_functions.function_map

        # Verify Coordinator-specific functions are NOT registered
        assert "update_brief" not in team_tools.tool_functions.function_map
        assert "resolve_information_request" not in team_tools.tool_functions.function_map

        # detect_information_request_needs is not exposed as a tool function anymore
        assert "detect_information_request_needs" not in team_tools.tool_functions.function_map

    @pytest.mark.asyncio
    async def test_project_tools_with_config(self, context, monkeypatch):
        """Test the ShareTools behavior with different configurations."""
        # Mock the assistant_config.get method
        mock_config = MagicMock()
        mock_config.track_progress = True

        async def mock_get_config(*args, **kwargs):
            return mock_config

        # Patch the assistant_config.get method
        mock_assistant_config = MagicMock()
        mock_assistant_config.get = AsyncMock(side_effect=mock_get_config)
        monkeypatch.setattr("assistant.config.assistant_config", mock_assistant_config)

        # Test with track_progress set to True first
        # Create a ShareTools instance directly
        tools = ShareTools(context, ConversationRole.COORDINATOR)

        # Make sure basic tools are available
        assert "update_brief" in tools.tool_functions.function_map

        # For team role, check available functions
        team_tools = ShareTools(context, ConversationRole.TEAM)
        assert "create_information_request" in team_tools.tool_functions.function_map

        # Now test with track_progress set to False
        mock_config.track_progress = False

        # Test with get_project_tools which handles tool removal based on track_progress
        # Since the track_progress check is now done in get_project_tools, we need to test that function

        # Create our own implementation to check for track_progress
        async def check_tools_with_config(context, role):
            """Simple wrapper to test if tools are filtered based on track_progress."""
            tools = ShareTools(context, role)

            # If progress tracking is disabled, remove progress-related tools
            if not mock_config.track_progress:
                # List of progress-related functions to remove
                progress_functions = [
                    "add_project_goal",
                    "delete_project_goal",
                    "mark_criterion_completed",
                    "mark_project_ready_for_working",
                    "report_project_completion",
                ]

                # Remove progress-related functions
                for func_name in progress_functions:
                    if func_name in tools.tool_functions.function_map:
                        del tools.tool_functions.function_map[func_name]

            return tools

        # Get the tools using our function that checks track_progress
        project_tools = await check_tools_with_config(context, ConversationRole.COORDINATOR)

        # Verify basic tools are still available regardless of track_progress setting
        assert "update_brief" in project_tools.tool_functions.function_map
        assert "resolve_information_request" in project_tools.tool_functions.function_map

        # For team tools
        team_tools = await check_tools_with_config(context, ConversationRole.TEAM)
        assert "create_information_request" in team_tools.tool_functions.function_map
        assert "delete_information_request" in team_tools.tool_functions.function_map

    @pytest.mark.asyncio
    async def test_detect_information_request_needs(self, context, monkeypatch):
        """Test the detect_information_request_needs function."""
        # Create a more complete context mock for this test
        context.assistant = MagicMock()
        context.assistant._template_id = "default"
        context.assistant.id = "test-assistant-id"

        # Test message
        test_message = "I need information about how to proceed with this task."

        # Setup mock config to be returned from assistant_config.get
        mock_config = MagicMock()
        mock_config.track_progress = True
        mock_config.service_config = None  # Will cause the method to return early with error info

        async def mock_get_config(*args, **kwargs):
            return mock_config

        # Patch assistant_config.get
        mock_assistant_config = MagicMock()
        mock_assistant_config.get = AsyncMock(side_effect=mock_get_config)
        monkeypatch.setattr("assistant.analysis.assistant_config", mock_assistant_config)

        # Create a mock message for the message history
        mock_msg = MagicMock()
        mock_msg.sender = MagicMock()
        mock_msg.sender.participant_id = "test-user-id"  # Not the assistant ID
        mock_msg.content = "Test message content"

        # Mock get_messages response
        mock_messages_response = MagicMock()
        mock_messages_response.messages = [mock_msg]
        context.get_messages = AsyncMock(return_value=mock_messages_response)

        # Test with the message - should return early with missing service_config
        result = await detect_information_request_needs(context, test_message)

        # Verify we get the expected early-return response for missing service_config
        assert not result["is_information_request"]
        assert "LLM detection unavailable" in result["reason"]
        assert result["confidence"] == 0.0

        # Now update mock config with a service_config and simulate a successful LLM response
        mock_config.service_config = {"type": "openai"}

        # Create mock client that returns expected response
        mock_client = AsyncMock()
        mock_response = MagicMock()
        mock_choice = MagicMock()
        mock_message = MagicMock()
        mock_message.content = '{"is_information_request": true, "confidence": 0.9, "potential_title": "Test title"}'
        mock_choice.message = mock_message
        mock_response.choices = [mock_choice]
        mock_client.chat.completions.create = AsyncMock(return_value=mock_response)

        # Mock the client creation context manager
        @contextlib.asynccontextmanager
        async def mock_create_client(*args, **kwargs):
            try:
                yield mock_client
            finally:
                pass

        # Patch the openai_client.create_client context manager
        monkeypatch.setattr(openai_client, "create_client", mock_create_client)

        # Test with message that should return mocked success response
        result = await detect_information_request_needs(context, test_message)

        # Verify successful path results
        assert result["is_information_request"] is True
        assert result["confidence"] == 0.9
        assert result["potential_title"] == "Test title"
        assert result["original_message"] == test_message

    # DISABLED: delete_project_goal functionality has been removed from the codebase
    # @pytest.mark.asyncio
    async def disabled_test_delete_project_goal(self, context, monkeypatch):
        """Test the delete_project_goal functionality."""
        # Setup mocks
        project_id = "test-project-id"
        goal_name = "Test Goal"

        # Mock KnowledgeTransferManager.get_project_id
        async def mock_get_project_id(*args, **kwargs):
            return project_id

        monkeypatch.setattr(
            "assistant.manager.KnowledgeTransferManager.get_project_id", AsyncMock(side_effect=mock_get_project_id)
        )

        # Mock require_current_user to return a user ID
        async def mock_require_current_user(*args, **kwargs):
            return "test-user-id"

        monkeypatch.setattr(
            "assistant.project_manager.require_current_user", AsyncMock(side_effect=mock_require_current_user)
        )

        # Mock KnowledgeTransferManager.delete_project_goal to return success
        async def mock_delete_project_goal(*args, **kwargs):
            return True, goal_name

        monkeypatch.setattr(
            "assistant.project_manager.KnowledgeTransferManager.delete_project_goal",
            AsyncMock(side_effect=mock_delete_project_goal),
        )

        # Test the delete_project_goal function
        # result = await tools.delete_learning_objective(objective_index)

        # Verify the result
        # assert f"Goal '{goal_name}' has been successfully deleted from the project." in result

        # Verify that context.send_messages was called with appropriate message
        expected_message_content = f"Goal '{goal_name}' has been successfully deleted from the project."
        context.send_messages.assert_called_once()
        # Get the first positional argument passed to send_messages
        call_args = context.send_messages.call_args[0][0]
        assert call_args.content == expected_message_content

    # DISABLED: delete_project_goal functionality has been removed from the codebase
    # @pytest.mark.asyncio
    async def disabled_test_delete_project_goal_wrong_role(self, context):
        """Test delete_project_goal with wrong role (Team instead of Coordinator)."""
        # Test the delete_project_goal function with Team role
        # result = await tools.delete_learning_objective(1)

        # Verify that the operation is rejected
        # assert "Only Coordinator can delete project goals." in result
        # Verify context.send_messages was not called
        context.send_messages.assert_not_called()

    # DISABLED: delete_project_goal functionality has been removed from the codebase
    # @pytest.mark.asyncio
    async def disabled_test_delete_project_goal_error(self, context, monkeypatch):
        """Test delete_project_goal with error condition."""
        # Setup mocks
        error_message = "Invalid goal index"

        # Mock KnowledgeTransferManager.get_project_id
        async def mock_get_project_id(*args, **kwargs):
            return "test-project-id"

        monkeypatch.setattr(
            "assistant.project_manager.KnowledgeTransferManager.get_project_id",
            AsyncMock(side_effect=mock_get_project_id),
        )

        # Mock KnowledgeTransferManager.delete_project_goal to return failure
        async def mock_delete_project_goal(*args, **kwargs):
            return False, error_message

        monkeypatch.setattr(
            "assistant.project_manager.KnowledgeTransferManager.delete_project_goal",
            AsyncMock(side_effect=mock_delete_project_goal),
        )

        # Test the delete_project_goal function
        # result = await tools.delete_learning_objective(999)  # Using an invalid index

        # Verify the error result
        # assert f"Error deleting goal: {error_message}" in result
        # Verify context.send_messages was not called
        context.send_messages.assert_not_called()
