# Copyright (c) Microsoft. All rights reserved.

import argparse
import asyncio
import logging
import time
from pathlib import Path

from assistant_data_gen.assistant_api import (
    create_test_jwt_token,
    get_all_messages,
    get_assistant,
    get_user_from_workbench_db,
    poll_assistant_status,
)
from assistant_data_gen.config import EvaluationConfig
from assistant_data_gen.gce.gce_agent import (
    Agenda,
    GuidedConversationInput,
    GuidedConversationState,
    step_conversation,
)
from dotenv import load_dotenv
from liquid import render
from semantic_workbench_api_model.workbench_model import (
    ConversationMessage,
    NewConversation,
    NewConversationMessage,
    ParticipantRole,
    UpdateParticipant,
)
from semantic_workbench_api_model.workbench_service_client import (
    UserRequestHeaders,
    WorkbenchServiceUserClientBuilder,
)

load_dotenv()

logger = logging.getLogger(__name__)

TURN_DELAY_SECONDS = 15


def get_last_assistant_message(messages: list[ConversationMessage]) -> str:
    """Get the last message from the document assistant."""
    for message in reversed(messages):
        if message.sender.participant_role == ParticipantRole.assistant:
            return message.content
    return ""


async def run_gce_simulation(
    config: EvaluationConfig,
    scenario_idx: int = 0,
) -> None:
    # Setup workbench client
    client_builder = WorkbenchServiceUserClientBuilder(
        base_url="http://127.0.0.1:3000",
        headers=UserRequestHeaders(token=create_test_jwt_token()),
    )

    # Get assistant and create conversation
    assistant = await get_assistant(client_builder, config.general.assistant_name)
    if assistant is None:
        raise ValueError(f"Assistant '{config.general.assistant_name}' not found")
    conversations_client = client_builder.for_conversations()
    conversation = await conversations_client.create_conversation(
        NewConversation(title=config.general.conversation_title)
    )

    # Add assistant to conversation
    conversation_client = client_builder.for_conversation(str(conversation.id))
    await conversation_client.update_participant(
        participant_id=str(assistant.id),
        participant=UpdateParticipant(active_participant=True),
    )
    await poll_assistant_status(conversation_client)

    # Setup GCE
    _, user_name = get_user_from_workbench_db()
    scenario_config = config.scenarios[scenario_idx]
    gce_context = render(
        config.general.gce_context,
        **{
            "user": user_name,
            "assistant_details": config.general.assistant_details,
            "scenario": scenario_config.description,
        },
    )
    gce_input = GuidedConversationInput(
        context=gce_context,
        rules=config.general.gce_rules,
        conversation_flow=scenario_config.gce_conversation_flow,
        resource_constraint_mode=config.general.resource_constraint_mode,
        provider=config.general.gce_provider,
    )
    gce_state = GuidedConversationState(
        agenda=Agenda(items=[]),
        message_history=[],
        resource_total=scenario_config.resource_total or config.general.resource_total,
    )

    # Init GCE and ignore its initial message
    gce_state = await step_conversation(gce_input, gce_state, user_message=None)
    gce_state.message_history = gce_state.message_history[:-1]
    while not gce_state.conversation_ended:
        # Get the assistant's last message (sending a message to the assistant auto-triggers a response)
        assistant_messages = await get_all_messages(conversation_client)
        last_assistant_message = get_last_assistant_message(assistant_messages)
        logger.info("Last assistant message: %s", last_assistant_message)

        # Get the GCE's next message based on the last document assistant message
        gce_state = await step_conversation(gce_input, gce_state, user_message=last_assistant_message)
        gce_message = gce_state.last_assistant_message or "Something went wrong. Please try again."
        logger.info("GCE generated message: %s", gce_message)
        logger.info("GCE Agenda\n%s", gce_state.agenda.format_for_llm())

        time.sleep(TURN_DELAY_SECONDS)

        # Send the GCE's message to the assistant
        await conversation_client.send_messages(NewConversationMessage(content=gce_message))
        await poll_assistant_status(conversation_client)


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(formatter_class=argparse.ArgumentDefaultsHelpFormatter)
    parser.add_argument(
        "--config",
        type=str,
        default=str(Path(__file__).parents[1] / "configs" / "document_assistant_example_config.yaml"),
        help="Path to the configuration YAML file",
    )
    parser.add_argument(
        "--scenario-idx",
        type=int,
        default=0,
        help="Index of scenario to use from config (defaults to 0)",
    )
    return parser.parse_args()


async def main() -> None:
    # Configure logging to show INFO messages from this module only
    logging.basicConfig(
        level=logging.WARNING,  # Set default level to WARNING to suppress most external logs
        format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
        handlers=[logging.StreamHandler()],
    )

    # Enable INFO logging only for this specific module
    logging.getLogger(__name__).setLevel(logging.INFO)

    # Explicitly silence noisy loggers
    logging.getLogger("httpx").setLevel(logging.WARNING)
    logging.getLogger("httpcore").setLevel(logging.WARNING)
    logging.getLogger("urllib3").setLevel(logging.WARNING)
    logging.getLogger("requests").setLevel(logging.WARNING)

    args = parse_args()
    config = EvaluationConfig.load_from_yaml(args.config)
    await run_gce_simulation(config=config, scenario_idx=args.scenario_idx)


if __name__ == "__main__":
    asyncio.run(main())
