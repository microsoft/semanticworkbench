"""
Test script to verify state inspector functionality.
"""

import asyncio
import logging
from unittest.mock import AsyncMock, MagicMock

from semantic_workbench_api_model.workbench_model import AssistantStateEvent
from semantic_workbench_assistant.assistant_app import ConversationContext

from assistant.assistant import assistant

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


async def test_inspector():
    """Test the state inspector provider."""
    # Create mock context
    context = AsyncMock(spec=ConversationContext)
    context.id = "test-conversation-id"
    context.assistant = MagicMock()
    context.assistant.id = "test-assistant-id"

    # Mock conversation
    conversation = MagicMock()
    conversation.metadata = {
        "setup_complete": True,
        "assistant_mode": "coordinator",
        "share_role": "coordinator",
    }
    context.get_conversation.return_value = conversation

    # Test all four tabbed inspectors
    inspector_ids = [
        "brief",
        "objectives",
        "requests",
        "debug",
    ]  # Note: "requests" tab now shows as "Sharing"

    for inspector_id in inspector_ids:
        logger.info(f"Testing {inspector_id} inspector...")

        # Create state event
        state_event = AssistantStateEvent(
            state_id=inspector_id, event="focus", state=None
        )

        # Send event
        logger.info("Sending state event...")
        await context.send_conversation_state_event(state_event)

        # Get inspector provider
        inspector_provider = assistant.inspector_state_providers.get(inspector_id)
        if not inspector_provider:
            logger.error(f"No {inspector_id} inspector provider found!")
            continue

        logger.info(f"Inspector provider found: {inspector_provider.display_name}")

        # Get state data
        try:
            state_data = await inspector_provider.get(context)
            logger.info(f"State data: {state_data}")
        except Exception as e:
            logger.error(f"Error getting state data: {e}")

        logger.info(f"--- {inspector_id} inspector test completed ---")


# Run the test
if __name__ == "__main__":
    asyncio.run(test_inspector())
