"""
Tests for the ProjectTools functionality.
"""

import json
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
        assert "update_project_status" not in coordinator_tools.tool_functions.function_map
        assert "mark_criterion_completed" not in coordinator_tools.tool_functions.function_map
        assert "report_project_completion" not in coordinator_tools.tool_functions.function_map

        # Test Team role
        team_tools = ProjectTools(context, "team")
        assert team_tools.role == "team"
        assert team_tools.tool_functions is not None

        # Verify Team-specific functions are registered
        assert "create_information_request" in team_tools.tool_functions.function_map
        assert "update_project_status" in team_tools.tool_functions.function_map
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
        # Test with default template
        # Test that get_project_tools returns a ProjectTools instance
        tools = await get_project_tools(context, "coordinator")
        assert isinstance(tools, ProjectTools)
        assert tools.role == "coordinator"
        # Verify progress functions are present with default template
        assert "add_project_goal" in tools.tool_functions.function_map
        assert "mark_project_ready_for_working" in tools.tool_functions.function_map

        # Now test with context transfer template by changing the template_id
        context.assistant._template_id = "context_transfer"
        tools = await get_project_tools(context, "coordinator")
        assert isinstance(tools, ProjectTools)
        assert tools.role == "coordinator"
        # Verify progress functions are removed with context_transfer template
        assert "add_project_goal" not in tools.tool_functions.function_map
        assert "mark_criterion_completed" not in tools.tool_functions.function_map

    @pytest.mark.asyncio
    async def test_detect_information_request_needs(self, context, monkeypatch):
        """Test the detect_information_request_needs function."""
        # Create the ProjectTools instance
        team_tools = ProjectTools(context, "team")

        # Patch the is_context_transfer_assistant function to return False for tests
        monkeypatch.setattr(
            "assistant.utils.is_context_transfer_assistant",
            lambda context: False
        )

        # Mock the assistant_config.get to avoid config issues
        mock_config = MagicMock()
        mock_config.service_config = MagicMock()

        async def mock_get_config(*args, **kwargs):
            return mock_config

        # Replace with our mock
        import assistant.project_tools as project_tools_module
        mock_assistant_config = MagicMock()
        mock_assistant_config.get = AsyncMock(side_effect=mock_get_config)
        monkeypatch.setattr(project_tools_module, "assistant_config", mock_assistant_config)

        # Mock text include to avoid file loading issues
        monkeypatch.setattr(
            "assistant.utils.load_text_include",
            lambda filename: "This is a test prompt"
        )

        # Mock the openai_client.create_client function to avoid LLM calls
        class MockAsyncContextManager:
            async def __aenter__(self):
                mock_client = MagicMock()
                # Set up the chat completions create method to return a valid response
                mock_completion = MagicMock()
                mock_choice = MagicMock()
                mock_message = MagicMock()
                mock_message.content = json.dumps({
                    "is_information_request": True,
                    "matched_indicators": ["need information"],
                    "potential_title": "I need information about",
                    "potential_description": "I need information about how to proceed with this task.",
                    "suggested_priority": "medium",
                    "confidence": 0.8
                })
                mock_choice.message = mock_message
                mock_completion.choices = [mock_choice]
                
                # Set up the nested structure for the async mock
                mock_chat = MagicMock()
                mock_chat.completions = MagicMock()
                mock_chat.completions.create = AsyncMock(return_value=mock_completion)
                mock_client.chat = mock_chat
                
                return mock_client

            async def __aexit__(self, exc_type, exc_val, exc_tb):
                pass

        # Patch the create_client function
        monkeypatch.setattr(
            "openai_client.create_client", 
            lambda service_config, **kwargs: MockAsyncContextManager()
        )

        # Test with a message that contains information request indicators
        test_message = "I need information about how to proceed with this task."
        result = await team_tools.detect_information_request_needs(test_message)

        assert result["is_information_request"]
        assert "potential_title" in result
        
        # Modify the mock to return a negative result for the second test
        class MockAsyncContextManagerNegative:
            async def __aenter__(self):
                mock_client = MagicMock()
                # Set up the chat completions create method to return a valid response
                mock_completion = MagicMock()
                mock_choice = MagicMock()
                mock_message = MagicMock()
                mock_message.content = json.dumps({
                    "is_information_request": False,
                    "reason": "No information request indicators found",
                    "confidence": 0.9
                })
                mock_choice.message = mock_message
                mock_completion.choices = [mock_choice]
                
                # Set up the nested structure for the async mock
                mock_chat = MagicMock()
                mock_chat.completions = MagicMock()
                mock_chat.completions.create = AsyncMock(return_value=mock_completion)
                mock_client.chat = mock_chat
                
                return mock_client

            async def __aexit__(self, exc_type, exc_val, exc_tb):
                pass

        # Update the patch for the second test
        monkeypatch.setattr(
            "openai_client.create_client", 
            lambda service_config, **kwargs: MockAsyncContextManagerNegative()
        )

        # Test with a message that doesn't contain information request indicators
        test_message = "Everything is going well with the project."
        result = await team_tools.detect_information_request_needs(test_message)

        assert not result["is_information_request"]
