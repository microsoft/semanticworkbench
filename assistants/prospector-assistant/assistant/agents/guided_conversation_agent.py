import json
import logging
from pathlib import Path
from typing import TYPE_CHECKING, Any

import deepmerge
import openai_client
from assistant.agents.guided_conversation.config import GuidedConversationAgentConfigModel
from guided_conversation.guided_conversation_agent import GuidedConversation
from openai import AsyncOpenAI
from openai.types.chat import ChatCompletionMessageParam
from semantic_kernel import Kernel
from semantic_kernel.connectors.ai.open_ai import OpenAIChatCompletion
from semantic_workbench_api_model.workbench_model import (
    AssistantStateEvent,
    MessageType,
    NewConversationMessage,
    ParticipantRole,
)
from semantic_workbench_assistant.assistant_app import (
    AssistantConversationInspectorStateDataModel,
    BaseModelAssistantConfig,
    ConversationContext,
    storage_directory_for_context,
)

logger = logging.getLogger(__name__)

if TYPE_CHECKING:
    from ..config import AssistantConfigModel, RequestConfig


#
# region Agent
#


class GuidedConversationAgent:
    """
    An agent for managing artifacts.
    """

    def __init__(
        self,
        config_provider: BaseModelAssistantConfig["AssistantConfigModel"],
    ) -> None:
        self.config_provider = config_provider

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
        conversation_context: ConversationContext,
        openai_client: AsyncOpenAI,
        request_config: "RequestConfig",
        agent_config: GuidedConversationAgentConfigModel,
        additional_messages: list[ChatCompletionMessageParam] | None = None,
    ) -> str | None:
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
            ai_model_id=request_config.openai_model,
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

        # Get the latest message from the user
        messages_response = await conversation_context.get_messages(limit=1, participant_role=ParticipantRole.user)
        last_user_message = messages_response.messages[0].content if messages_response.messages else None

        # Step the conversation to start the conversation with the agent
        result = await guided_conversation_agent.step_conversation(last_user_message)

        # Save the state of the guided conversation agent
        _write_guided_conversation_state(conversation_context, guided_conversation_agent.to_json())

        return result.ai_message

    # endregion

    #
    # region Response
    #

    # demonstrates how to respond to a conversation message using the guided conversation library
    async def respond_to_conversation(
        self,
        context: ConversationContext,
        metadata: dict[str, Any] = {},
        additional_messages: list[ChatCompletionMessageParam] | None = None,
    ) -> None:
        """
        Respond to a conversation message.

        This method uses the guided conversation agent to respond to a conversation message. The guided conversation
        agent is designed to guide the conversation towards a specific goal as specified in its definition.
        """

        # define the metadata key for any metadata created within this method
        method_metadata_key = "respond_to_conversation"

        # get the assistant configuration
        assistant_config = await self.config_provider.get(context.assistant)

        # initialize variables for the response content
        content: str | None = None

        try:
            content = await self.step_conversation(
                conversation_context=context,
                openai_client=openai_client.create_client(assistant_config.service_config),
                request_config=assistant_config.request_config,
                agent_config=assistant_config.agents_config.guided_conversation_agent,
                additional_messages=additional_messages,
            )
            # add the completion to the metadata for debugging
            deepmerge.always_merger.merge(
                metadata,
                {
                    "debug": {
                        f"{method_metadata_key}": {"response": content},
                    }
                },
            )
        except Exception as e:
            logger.exception(f"exception occurred processing guided conversation: {e}")
            content = "An error occurred while processing the guided conversation."
            deepmerge.always_merger.merge(
                metadata,
                {
                    "debug": {
                        f"{method_metadata_key}": {
                            "error": str(e),
                        },
                    }
                },
            )

        # add the state to the metadata for debugging
        state = self.get_state(context)
        deepmerge.always_merger.merge(
            metadata,
            {
                "debug": {
                    f"{method_metadata_key}": {
                        "state": state,
                    },
                }
            },
        )

        # send the response to the conversation
        await context.send_messages(
            NewConversationMessage(
                content=content or "[no response from assistant]",
                message_type=MessageType.chat if content else MessageType.note,
                metadata=metadata,
            )
        )

        await context.send_conversation_state_event(
            AssistantStateEvent(
                state_id="guided_conversation",
                event="updated",
                state=None,
            )
        )


# endregion


#
# region Inspector
#


class GuidedConversationConversationInspectorStateProvider:
    display_name = "Guided Conversation"
    description = "State of the guided conversation feature within the conversation."

    def __init__(
        self,
        config_provider: BaseModelAssistantConfig["AssistantConfigModel"],
    ) -> None:
        self.config_provider = config_provider

    async def get(self, context: ConversationContext) -> AssistantConversationInspectorStateDataModel:
        """
        Get the state for the conversation.
        """

        state = _read_guided_conversation_state(context)

        return AssistantConversationInspectorStateDataModel(data=state or {"content": "No state available."})


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
