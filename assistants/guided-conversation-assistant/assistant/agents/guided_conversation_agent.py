import json
import pathlib
from pathlib import Path
from typing import TYPE_CHECKING, Annotated, Literal

from assistant.agents.guided_conversation.artifact_poem_feedback import ArtifactPoemFeedback
from guided_conversation.guided_conversation_agent import GuidedConversation
from guided_conversation.utils.resources import ResourceConstraint, ResourceConstraintMode, ResourceConstraintUnit
from openai import AsyncAzureOpenAI
from pydantic import BaseModel, Field
from semantic_kernel import Kernel
from semantic_kernel.connectors.ai.open_ai import AzureChatCompletion
from semantic_workbench_api_model.workbench_model import ConversationMessage, ParticipantRole
from semantic_workbench_assistant.assistant_app import (
    AssistantConversationInspectorStateDataModel,
    BaseModelAssistantConfig,
    ConversationContext,
    FileStorageContext,
)
from semantic_workbench_assistant.config import UISchema

if TYPE_CHECKING:
    from ..config import AssistantConfigModel


#
# region Helpers
#


# helper for loading an include from a text file
def load_text_include(filename) -> str:
    # get directory relative to this module
    directory = pathlib.Path(__file__).parent.parent

    # get the file path for the prompt file
    file_path = directory / "text_includes" / filename

    # read the prompt from the file
    return file_path.read_text()


# endregion


#
# region Models
#


class GuidedConversationAgentConfigModel(BaseModel):
    gc_rules: Annotated[
        list[str],
        Field(title="Rules", description="Do's and don'ts that the agent should attempt to follow"),
    ] = []

    gc_starter_message: Annotated[
        str,
        Field(
            title="Starter Message",
            description="The message that will be sent to the user when the conversation starts.",
        ),
    ] = "Welcome!"

    gc_conversation_flow: Annotated[
        str,
        Field(
            title="Conversation Flow",
            description="A loose natural language description of the steps of the conversation",
        ),
        UISchema(placeholder="[optional]"),
    ] = ""

    gc_context: Annotated[
        str,
        Field(
            title="Context",
            description="General background context for the conversation.",
        ),
        UISchema(placeholder="[optional]"),
    ] = ""

    class ResourceConstraint(ResourceConstraint):
        gc_resource_mode: Annotated[
            Literal["maximum", "exact", "none"],
            Field(
                title="Resource Mode",
                description=(
                    'If "exact", the agents will try to pace the conversation to use exactly the resource quantity. If'
                    ' "maximum", the agents will try to pace the conversation to use at most the resource quantity.'
                ),
            ),
        ] = "exact"

        gc_resource_unit: Annotated[
            Literal["seconds", "minutes", "turns"],
            Field(
                title="Resource Unit",
                description="The unit for the resource constraint.",
            ),
        ] = "turns"

        gc_resource_quantity: Annotated[
            float,
            Field(
                title="Resource Quantity",
                description="The quantity for the resource constraint. If <=0, the resource constraint is disabled.",
            ),
        ] = 0.0

    resource_constraint: Annotated[
        ResourceConstraint,
        Field(
            title="Resource Constraint",
        ),
    ] = ResourceConstraint(
        quantity=0,
        unit=ResourceConstraintUnit.TURNS,
        mode=ResourceConstraintMode.EXACT,
    )


# endregion


#
# region Agent
#


class GuidedConversationAgent:
    """
    An agent for managing artifacts.
    """

    @staticmethod
    async def step_conversation(
        conversation_context: ConversationContext,
        conversation: list[ConversationMessage],
        openai_client: AsyncAzureOpenAI,
        agent_config: GuidedConversationAgentConfigModel,
    ) -> None:
        """
        Step the conversation to the next turn.
        """

        rules = agent_config.gc_rules
        conversation_flow = agent_config.gc_conversation_flow
        context = agent_config.gc_context

        if (
            agent_config.resource_constraint.gc_resource_mode != "none"
            and agent_config.resource_constraint.gc_resource_quantity > 0
        ):
            match agent_config.resource_constraint.gc_resource_mode:
                case "maximum":
                    mode = ResourceConstraintMode.MAXIMUM
                case "exact":
                    mode = ResourceConstraintMode.EXACT

            match agent_config.resource_constraint.gc_resource_unit:
                case "seconds":
                    unit = ResourceConstraintUnit.SECONDS
                case "minutes":
                    unit = ResourceConstraintUnit.MINUTES
                case "turns":
                    unit = ResourceConstraintUnit.TURNS

            resource_constraint = ResourceConstraint(
                quantity=agent_config.resource_constraint.gc_resource_quantity,
                unit=unit,
                mode=mode,
            )
        else:
            resource_constraint = None

        kernel = Kernel()
        service_id = "gc_main"

        chat_service = AzureChatCompletion(
            async_client=openai_client,
        )
        kernel.add_service(chat_service)

        guided_conversation_agent: GuidedConversation

        state = _read_guided_conversation_state(conversation_context)
        if state:
            guided_conversation_agent = GuidedConversation.from_json(
                json_data=state,
                kernel=kernel,
                service_id=service_id,
            )
        else:
            guided_conversation_agent = GuidedConversation(
                kernel=kernel,
                artifact=ArtifactPoemFeedback,  # type: ignore
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
        print(f"Assistant: {result.ai_message}")

        # Save the state of the guided conversation agent
        _write_guided_conversation_state(conversation_context, guided_conversation_agent.to_json())


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
    path = FileStorageContext.get(context).directory / "guided-conversation"
    if filename:
        path /= filename
    return path


def _write_guided_conversation_state(context: ConversationContext, state: dict) -> None:
    """
    Write the state of the guided conversation agent to a file.
    """
    _get_guided_conversation_storage_path(context, "state.json").write_text(json.dumps(state))


def _read_guided_conversation_state(context: ConversationContext) -> dict | None:
    """
    Read the state of the guided conversation agent from a file.
    """
    path = _get_guided_conversation_storage_path(context, "state.json")
    if path.exists():
        try:
            return json.loads(path.read_text())
        except Exception:
            pass
    return None


# endregion
