import json
import logging
from pathlib import Path

from guided_conversation.guided_conversation_agent import GuidedConversation
from openai import AsyncOpenAI
from semantic_kernel import Kernel
from semantic_kernel.connectors.ai.open_ai import OpenAIChatCompletion
from semantic_workbench_assistant.assistant_app import (
    ConversationContext,
    storage_directory_for_context,
)

from ...config import AssistantConfigModel
from .config import GuidedConversationAgentConfigModel

logger = logging.getLogger(__name__)


#
# region Agent
#


class GuidedConversationAgent:
    """
    An agent for managing artifacts.
    """

    @staticmethod
    def get_state(
        conversation_context: ConversationContext,
    ) -> dict | None:
        """
        Get the state of the guided conversation agent.
        """
        return _read_guided_conversation_state(conversation_context)

    @staticmethod
    async def step_conversation(
        config: AssistantConfigModel,
        openai_client: AsyncOpenAI,
        agent_config: GuidedConversationAgentConfigModel,
        conversation_context: ConversationContext,
        last_user_message: str | None,
    ) -> tuple[str | None, bool]:
        """
        Step the conversation to the next turn.
        """

        rules = agent_config.rules
        conversation_flow = agent_config.conversation_flow
        context = agent_config.context
        resource_constraint = agent_config.resource_constraint
        artifact = agent_config.get_artifact_model()

        kernel = Kernel()
        service_id = "gc_main"

        chat_service = OpenAIChatCompletion(
            service_id=service_id,
            async_client=openai_client,
            ai_model_id=config.request_config.openai_model,
        )
        kernel.add_service(chat_service)

        guided_conversation_agent: GuidedConversation

        state = _read_guided_conversation_state(conversation_context)
        if state:
            guided_conversation_agent = GuidedConversation.from_json(
                json_data=state,
                kernel=kernel,
                artifact=artifact,  # type: ignore
                conversation_flow=conversation_flow,
                context=context,
                rules=rules,
                resource_constraint=resource_constraint,
                service_id=service_id,
            )
        else:
            guided_conversation_agent = GuidedConversation(
                kernel=kernel,
                artifact=artifact,  # type: ignore
                conversation_flow=conversation_flow,
                context=context,
                rules=rules,
                resource_constraint=resource_constraint,
                service_id=service_id,
            )

        # Step the conversation to start the conversation with the agent
        # or message
        result = await guided_conversation_agent.step_conversation(last_user_message)

        # Save the state of the guided conversation agent
        _write_guided_conversation_state(conversation_context, guided_conversation_agent.to_json())

        return result.ai_message, result.is_conversation_over

    # endregion


#
# region Helpers
#


def _get_guided_conversation_storage_path(context: ConversationContext, filename: str | None = None) -> Path:
    """
    Get the path to the directory for storing guided conversation files.
    """
    path = storage_directory_for_context(context) / "guided-conversation"
    if filename:
        path /= filename
    return path


def _write_guided_conversation_state(context: ConversationContext, state: dict) -> None:
    """
    Write the state of the guided conversation agent to a file.
    """
    json_data = json.dumps(state)
    path = _get_guided_conversation_storage_path(context)
    if not path.exists():
        path.mkdir(parents=True)
    path = path / "state.json"
    path.write_text(json_data)


def _read_guided_conversation_state(context: ConversationContext) -> dict | None:
    """
    Read the state of the guided conversation agent from a file.
    """
    path = _get_guided_conversation_storage_path(context, "state.json")
    if path.exists():
        try:
            json_data = path.read_text()
            return json.loads(json_data)
        except Exception:
            pass
    return None


# endregion
