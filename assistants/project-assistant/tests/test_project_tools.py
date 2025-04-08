"""
Tests for the ProjectTools functionality.
"""

from unittest.mock import AsyncMock, MagicMock

import pytest
from assistant.project_tools import ProjectTools, get_project_tools
from semantic_workbench_assistant.assistant_app import ConversationContext


# Use pytest for all tests for consistency
class TestProjectTools:
    """Test the ProjectTools class."""

    @pytest.fixture
    def context(self):
        """Set up test fixtures."""
        context = AsyncMock(spec=ConversationContext)
        context.conversation = MagicMock()
        context.id = "test-conversation-id"
        # Add the assistant attribute for the get_project_tools test
        context.assistant = MagicMock()
        # Use the correct property name (_template_id)
        context.assistant._template_id = "default"
        return context

    def test_initialization(self, context):
        """Test that ProjectTools initializes correctly."""
        # Test Coordinator role
        coordinator_tools = ProjectTools(context, "coordinator")
        assert coordinator_tools.role == "coordinator"
        assert coordinator_tools.tool_functions is not None

        # Verify Coordinator-specific functions are registered
        assert "create_project_brief" in coordinator_tools.tool_functions.function_map
        assert "add_project_goal" in coordinator_tools.tool_functions.function_map
        assert "resolve_information_request" in coordinator_tools.tool_functions.function_map
        assert "mark_project_ready_for_working" in coordinator_tools.tool_functions.function_map

        # Verify Team-specific functions are NOT registered
        assert "create_information_request" not in coordinator_tools.tool_functions.function_map
        assert "update_project_dashboard" not in coordinator_tools.tool_functions.function_map
        assert "mark_criterion_completed" not in coordinator_tools.tool_functions.function_map
        assert "report_project_completion" not in coordinator_tools.tool_functions.function_map

        # Test Team role
        team_tools = ProjectTools(context, "team")
        assert team_tools.role == "team"
        assert team_tools.tool_functions is not None

        # Verify Team-specific functions are registered
        assert "create_information_request" in team_tools.tool_functions.function_map
        assert "update_project_dashboard" in team_tools.tool_functions.function_map
        assert "mark_criterion_completed" in team_tools.tool_functions.function_map
        assert "report_project_completion" in team_tools.tool_functions.function_map

        # Verify Coordinator-specific functions are NOT registered
        assert "create_project_brief" not in team_tools.tool_functions.function_map
        assert "add_project_goal" not in team_tools.tool_functions.function_map
        assert "resolve_information_request" not in team_tools.tool_functions.function_map
        assert "mark_project_ready_for_working" not in team_tools.tool_functions.function_map

        # Verify common functions are registered for both roles
        assert "get_project_info" in coordinator_tools.tool_functions.function_map
        assert "suggest_next_action" in coordinator_tools.tool_functions.function_map

        # Verify team detection tool is not in Coordinator tools
        assert "detect_information_request_needs" not in coordinator_tools.tool_functions.function_map

        assert "get_project_info" in team_tools.tool_functions.function_map
        assert "suggest_next_action" in team_tools.tool_functions.function_map

        # Verify team-specific detection tool
        assert "detect_information_request_needs" in team_tools.tool_functions.function_map

    @pytest.mark.asyncio
    async def test_get_project_tools(self, context, monkeypatch):
        """Test the get_project_tools factory function."""
        # Mock the assistant_config.get method
        mock_config = MagicMock()
        mock_config.track_progress = True

        async def mock_get_config(*args, **kwargs):
            return mock_config

        # Patch the assistant_config.get method directly since it's now imported at the top level
        # Import the module where get_project_tools is defined to patch the assistant_config
        import assistant.project_tools as project_tools_module

        # Replace with our mock
        mock_assistant_config = MagicMock()
        mock_assistant_config.get = AsyncMock(side_effect=mock_get_config)
        project_tools_module.assistant_config = mock_assistant_config

        # Ensure we restore the original when the test is done
        monkeypatch.setattr(project_tools_module, "assistant_config", mock_assistant_config)

        # Test that get_project_tools returns a ProjectTools instance
        tools = await get_project_tools(context, "coordinator")
        assert isinstance(tools, ProjectTools)
        assert tools.role == "coordinator"

        # Test with track_progress set to False
        mock_config.track_progress = False
        tools = await get_project_tools(context, "coordinator")
        assert isinstance(tools, ProjectTools)
        assert tools.role == "coordinator"
        # Verify progress functions are removed
        assert "add_project_goal" not in tools.tool_functions.function_map
        assert "mark_criterion_completed" not in tools.tool_functions.function_map

    @pytest.mark.asyncio
    async def test_detect_information_request_needs(self, context):
        """Test the detect_information_request_needs function."""
        team_tools = ProjectTools(context, "team")

        # Test with a message that contains information request indicators
        test_message = "I need information about how to proceed with this task."
        result = await team_tools.detect_information_request_needs(test_message)

        assert result["is_information_request"]
        assert "need information" in result["matched_indicators"]

        # Test with a message that doesn't contain information request indicators
        test_message = "Everything is going well with the project."
        result = await team_tools.detect_information_request_needs(test_message)

        assert not result["is_information_request"]
