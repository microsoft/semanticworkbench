"""
Tests for the ProjectTools functionality.
"""

import json
from unittest.mock import AsyncMock, MagicMock

import pytest
from assistant.project_tools import ProjectTools
from semantic_workbench_assistant.assistant_app import ConversationContext
from assistant.config import assistant_config


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
        assert "update_project_info" in team_tools.tool_functions.function_map  # Updated from update_project_dashboard
        assert "mark_criterion_completed" in team_tools.tool_functions.function_map
        assert "report_project_completion" in team_tools.tool_functions.function_map
        assert "delete_information_request" in team_tools.tool_functions.function_map  # Added new function
        assert "view_coordinator_conversation" in team_tools.tool_functions.function_map  # Added new function

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
    async def test_project_tools_with_config(self, context, monkeypatch):
        """Test the ProjectTools behavior with different configurations."""
        # Mock the assistant_config.get method
        mock_config = MagicMock()
        mock_config.track_progress = True

        async def mock_get_config(*args, **kwargs):
            return mock_config

        # Patch the assistant_config.get method
        mock_assistant_config = MagicMock()
        mock_assistant_config.get = AsyncMock(side_effect=mock_get_config)
        monkeypatch.setattr("assistant.project_tools.assistant_config", mock_assistant_config)

        # Test with track_progress set to True first
        # Create a ProjectTools instance directly
        tools = ProjectTools(context, "coordinator")
        
        # Make sure add_project_goal was added when track_progress=True
        assert "add_project_goal" in tools.tool_functions.function_map
        
        # For team role, check criterion completion
        team_tools = ProjectTools(context, "team")
        assert "mark_criterion_completed" in team_tools.tool_functions.function_map
        
        # Now test with track_progress set to False
        mock_config.track_progress = False
        
        # For add_project_goal, we need to monkey patch the check in the method
        # Since we're now testing a method that uses await assistant_config.get() 
        # We'll monkeypatch the method directly to simulate track_progress=False
        
        # Create a test instance that will be configured during the async call
        coordinator_tools = ProjectTools(context, "coordinator")
        team_tools = ProjectTools(context, "team")
        
        # Test the add_project_goal method with track_progress=False
        result = await coordinator_tools.add_project_goal("Test Goal", "Test Description", ["Test Criterion"])
        assert "Progress tracking is not enabled" in result
        
        # Test the mark_criterion_completed method with track_progress=False
        result = await team_tools.mark_criterion_completed(0, 0)
        assert "Progress tracking is not enabled" in result

    @pytest.mark.asyncio
    async def test_detect_information_request_needs(self, context, monkeypatch):
        """Test the detect_information_request_needs function."""
        # Create the ProjectTools instance
        team_tools = ProjectTools(context, "team")
        
        # Patch the assistant_config.get method to avoid actual config loading
        mock_config = MagicMock()
        mock_config.track_progress = True
        mock_config.service_config = None  # Ensure we use the fallback keyword detection

        async def mock_get_config(*args, **kwargs):
            return mock_config

        # Patch assistant_config.get
        mock_assistant_config = MagicMock()
        mock_assistant_config.get = AsyncMock(side_effect=mock_get_config)
        monkeypatch.setattr("assistant.project_tools.assistant_config", mock_assistant_config)
        
        # Force using the simple keyword detection by making sure we'll hit the exception path
        # This avoids the need to mock the entire openai client infrastructure
        monkeypatch.setattr(team_tools, "_simple_keyword_detection", MagicMock(return_value={
            "is_information_request": True,
            "matched_indicators": ["need information"],
            "potential_title": "I need information about",
            "potential_description": "I need information about how to proceed with this task.",
            "suggested_priority": "medium",
            "confidence": 0.6
        }))

        # Test with a message that contains information request indicators
        test_message = "I need information about how to proceed with this task."
        result = await team_tools.detect_information_request_needs(test_message)

        assert result["is_information_request"]
        # Check that the simple keyword detection was used
        assert result["confidence"] == 0.6
        
        # Now test negative case
        monkeypatch.setattr(team_tools, "_simple_keyword_detection", MagicMock(return_value={
            "is_information_request": False,
            "reason": "No information request indicators found"
        }))

        # Test with a message that doesn't contain information request indicators
        test_message = "Everything is going well with the project."
        result = await team_tools.detect_information_request_needs(test_message)

        assert not result["is_information_request"]
