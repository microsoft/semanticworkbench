"""
Tests for the MissionTools functionality.
"""

import unittest
from unittest.mock import AsyncMock, MagicMock

import pytest
from assistant.mission_tools import MissionTools, get_mission_tools
from semantic_workbench_assistant.assistant_app import ConversationContext


class TestMissionTools(unittest.TestCase):
    """Test the MissionTools class."""

    def setUp(self):
        """Set up test fixtures."""
        self.context = AsyncMock(spec=ConversationContext)
        self.context.conversation = MagicMock()
        self.context.id = "test-conversation-id"

    def test_initialization(self):
        """Test that MissionTools initializes correctly."""
        # Test HQ role
        hq_tools = MissionTools(self.context, "hq")
        self.assertEqual(hq_tools.role, "hq")
        self.assertIsNotNone(hq_tools.tool_functions)

        # Verify HQ-specific functions are registered
        self.assertIn("create_mission_briefing", hq_tools.tool_functions.function_map)
        self.assertIn("add_mission_goal", hq_tools.tool_functions.function_map)
        self.assertIn("add_kb_section", hq_tools.tool_functions.function_map)
        self.assertIn("resolve_field_request", hq_tools.tool_functions.function_map)
        self.assertIn("mark_mission_ready_for_field", hq_tools.tool_functions.function_map)

        # Verify Field-specific functions are NOT registered
        self.assertNotIn("create_field_request", hq_tools.tool_functions.function_map)
        self.assertNotIn("update_mission_status", hq_tools.tool_functions.function_map)
        self.assertNotIn("mark_criterion_completed", hq_tools.tool_functions.function_map)
        self.assertNotIn("report_mission_completion", hq_tools.tool_functions.function_map)

        # Test Field role
        field_tools = MissionTools(self.context, "field")
        self.assertEqual(field_tools.role, "field")
        self.assertIsNotNone(field_tools.tool_functions)

        # Verify Field-specific functions are registered
        self.assertIn("create_field_request", field_tools.tool_functions.function_map)
        self.assertIn("update_mission_status", field_tools.tool_functions.function_map)
        self.assertIn("mark_criterion_completed", field_tools.tool_functions.function_map)
        self.assertIn("report_mission_completion", field_tools.tool_functions.function_map)

        # Verify HQ-specific functions are NOT registered
        self.assertNotIn("create_mission_briefing", field_tools.tool_functions.function_map)
        self.assertNotIn("add_mission_goal", field_tools.tool_functions.function_map)
        self.assertNotIn("add_kb_section", field_tools.tool_functions.function_map)
        self.assertNotIn("resolve_field_request", field_tools.tool_functions.function_map)
        self.assertNotIn("mark_mission_ready_for_field", field_tools.tool_functions.function_map)

        # Verify common functions are registered for both roles
        self.assertIn("get_mission_info", hq_tools.tool_functions.function_map)
        self.assertIn("suggest_next_action", hq_tools.tool_functions.function_map)
        self.assertIn("detect_field_request_needs", hq_tools.tool_functions.function_map)

        self.assertIn("get_mission_info", field_tools.tool_functions.function_map)
        self.assertIn("suggest_next_action", field_tools.tool_functions.function_map)
        self.assertIn("detect_field_request_needs", field_tools.tool_functions.function_map)

    @pytest.mark.asyncio
    async def test_get_mission_tools(self) -> None:
        """Test the get_mission_tools factory function."""
        # Test that get_mission_tools returns a MissionTools instance
        tools = await get_mission_tools(self.context, "hq")
        self.assertIsInstance(tools, MissionTools)
        self.assertEqual(tools.role, "hq")

    @pytest.mark.asyncio
    async def test_detect_field_request_needs(self) -> None:
        """Test the detect_field_request_needs function."""
        field_tools = MissionTools(self.context, "field")

        # Test with a message that contains field request indicators
        test_message = "I need information about how to proceed with this task."
        result = await field_tools.detect_field_request_needs(test_message)

        self.assertTrue(result["is_field_request"])
        self.assertIn("need information", result["matched_indicators"])

        # Test with a message that doesn't contain field request indicators
        test_message = "Everything is going well with the mission."
        result = await field_tools.detect_field_request_needs(test_message)

        self.assertFalse(result["is_field_request"])


if __name__ == "__main__":
    unittest.main()
