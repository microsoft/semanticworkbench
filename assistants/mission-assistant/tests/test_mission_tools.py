"""
Tests for the MissionTools functionality.
"""

from unittest.mock import AsyncMock, MagicMock

import pytest
from assistant.mission_tools import MissionTools, get_mission_tools
from semantic_workbench_assistant.assistant_app import ConversationContext


# Use pytest for all tests for consistency
class TestMissionTools:
    """Test the MissionTools class."""

    @pytest.fixture
    def context(self):
        """Set up test fixtures."""
        context = AsyncMock(spec=ConversationContext)
        context.conversation = MagicMock()
        context.id = "test-conversation-id"
        return context

    def test_initialization(self, context):
        """Test that MissionTools initializes correctly."""
        # Test HQ role
        hq_tools = MissionTools(context, "hq")
        assert hq_tools.role == "hq"
        assert hq_tools.tool_functions is not None

        # Verify HQ-specific functions are registered
        assert "create_mission_briefing" in hq_tools.tool_functions.function_map
        assert "add_mission_goal" in hq_tools.tool_functions.function_map
        assert "add_kb_section" in hq_tools.tool_functions.function_map
        assert "resolve_field_request" in hq_tools.tool_functions.function_map
        assert "mark_mission_ready_for_field" in hq_tools.tool_functions.function_map

        # Verify Field-specific functions are NOT registered
        assert "create_field_request" not in hq_tools.tool_functions.function_map
        assert "update_mission_status" not in hq_tools.tool_functions.function_map
        assert "mark_criterion_completed" not in hq_tools.tool_functions.function_map
        assert "report_mission_completion" not in hq_tools.tool_functions.function_map

        # Test Field role
        field_tools = MissionTools(context, "field")
        assert field_tools.role == "field"
        assert field_tools.tool_functions is not None

        # Verify Field-specific functions are registered
        assert "create_field_request" in field_tools.tool_functions.function_map
        assert "update_mission_status" in field_tools.tool_functions.function_map
        assert "mark_criterion_completed" in field_tools.tool_functions.function_map
        assert "report_mission_completion" in field_tools.tool_functions.function_map

        # Verify HQ-specific functions are NOT registered
        assert "create_mission_briefing" not in field_tools.tool_functions.function_map
        assert "add_mission_goal" not in field_tools.tool_functions.function_map
        assert "add_kb_section" not in field_tools.tool_functions.function_map
        assert "resolve_field_request" not in field_tools.tool_functions.function_map
        assert "mark_mission_ready_for_field" not in field_tools.tool_functions.function_map

        # Verify common functions are registered for both roles
        assert "get_mission_info" in hq_tools.tool_functions.function_map
        assert "suggest_next_action" in hq_tools.tool_functions.function_map
        assert "detect_field_request_needs" in hq_tools.tool_functions.function_map

        assert "get_mission_info" in field_tools.tool_functions.function_map
        assert "suggest_next_action" in field_tools.tool_functions.function_map
        assert "detect_field_request_needs" in field_tools.tool_functions.function_map

    @pytest.mark.asyncio
    async def test_get_mission_tools(self, context):
        """Test the get_mission_tools factory function."""
        # Test that get_mission_tools returns a MissionTools instance
        tools = await get_mission_tools(context, "hq")
        assert isinstance(tools, MissionTools)
        assert tools.role == "hq"

    @pytest.mark.asyncio
    async def test_detect_field_request_needs(self, context):
        """Test the detect_field_request_needs function."""
        field_tools = MissionTools(context, "field")

        # Test with a message that contains field request indicators
        test_message = "I need information about how to proceed with this task."
        result = await field_tools.detect_field_request_needs(test_message)

        assert result["is_field_request"]
        assert "need information" in result["matched_indicators"]

        # Test with a message that doesn't contain field request indicators
        test_message = "Everything is going well with the mission."
        result = await field_tools.detect_field_request_needs(test_message)

        assert not result["is_field_request"]
