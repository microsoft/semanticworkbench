import json
import logging
from enum import StrEnum
from pathlib import Path

from guided_conversation.guided_conversation_agent import GuidedConversation as GuidedConversationAgent
from openai import AsyncOpenAI
from pydantic import BaseModel
from semantic_kernel import Kernel
from semantic_kernel.connectors.ai.open_ai import OpenAIChatCompletion
from semantic_workbench_assistant.assistant_app import (
    ConversationContext,
    storage_directory_for_context,
)

from ...config import AssistantConfigModel
from .config import GuidedConversationConfigModel

logger = logging.getLogger(__name__)


#
# region Agent
#
class GC_ConversationStatus(StrEnum):
    UNDEFINED = "undefined"
    USER_INITIATED = "user_initiated"
    USER_RETURNED = "user_returned"
    USER_COMPLETED = "user_completed"


class GC_UserDecision(StrEnum):
    UNDEFINED = "undefined"
    UPDATE_OUTLINE = "update_outline"
    DRAFT_PAPER = "draft_paper"
    UPDATE_CONTENT = "update_content"
    DRAFT_NEXT_CONTENT = "draft_next_content"
    EXIT_EARLY = "exit_early"


class GuidedConversation:
    """
    An agent for managing artifacts.
    """

    def __init__(
        self,
        config: AssistantConfigModel,
        openai_client: AsyncOpenAI,
        agent_config: GuidedConversationConfigModel,
        artifact_model: type[BaseModel],
        conversation_context: ConversationContext,
        artifact_updates: dict = {},
    ) -> None:
        self.guided_conversation_agent: GuidedConversationAgent
        self.conversation_context: ConversationContext = conversation_context

        self.kernel = Kernel()
        self.service_id = "gc_main"

        chat_service = OpenAIChatCompletion(
            service_id=self.service_id,
            async_client=openai_client,
            ai_model_id=config.request_config.openai_model,
        )
        self.kernel.add_service(chat_service)

        self.artifact_model = artifact_model
        self.conversation_flow = agent_config.conversation_flow
        self.context = agent_config.context
        self.rules = agent_config.rules
        self.resource_constraint = agent_config.resource_constraint

        state = _read_guided_conversation_state(conversation_context)
        if not state:
            self.guided_conversation_agent = GuidedConversationAgent(
                kernel=self.kernel,
                artifact=self.artifact_model,
                conversation_flow=self.conversation_flow,
                context=self.context,
                rules=self.rules,
                resource_constraint=self.resource_constraint,
                service_id=self.service_id,
            )
            state = self.guided_conversation_agent.to_json()

        if artifact_updates:
            state["artifact"]["artifact"].update(artifact_updates)

        self.guided_conversation_agent = GuidedConversationAgent.from_json(
            json_data=state,
            kernel=self.kernel,
            artifact=self.artifact_model,
            conversation_flow=self.conversation_flow,
            context=self.context,
            rules=self.rules,
            resource_constraint=self.resource_constraint,
            service_id=self.service_id,
        )
        return

    async def step_conversation(
        self,
        last_user_message: str | None,
    ) -> tuple[str, GC_ConversationStatus, GC_UserDecision]:
        """
        Step the conversation to the next turn.
        """
        # Step the conversation to start the conversation with the agent
        # or message
        result = await self.guided_conversation_agent.step_conversation(last_user_message)

        # Save the state of the guided conversation agent
        _write_guided_conversation_state(self.conversation_context, self.guided_conversation_agent.to_json())

        # convert information in artifact for Document Agent
        # conversation_status:  # this should relate to result.is_conversation_over
        # final_response:  # replace result.ai_message with final_response if "user_completed"

        final_response: str = ""
        conversation_status_str: str | None = None
        user_decision_str: str | None = None
        response: str = ""

        # to_json is actually to dict
        gc_dict = self.guided_conversation_agent.to_json()
        artifact_item = gc_dict.get("artifact")
        if artifact_item is not None:
            artifact_item = artifact_item.get("artifact")
            if artifact_item is not None:
                final_response = artifact_item.get("final_response")
                conversation_status_str = artifact_item.get("conversation_status")
                user_decision_str = artifact_item.get("user_decision")

        gc_conversation_status = GC_ConversationStatus.UNDEFINED
        gc_user_decision: GC_UserDecision = GC_UserDecision.UNDEFINED
        if conversation_status_str is not None:
            match conversation_status_str:
                case GC_ConversationStatus.USER_COMPLETED:
                    response = final_response or result.ai_message or ""
                    gc_conversation_status = GC_ConversationStatus.USER_COMPLETED
                    match user_decision_str:
                        case GC_UserDecision.UPDATE_OUTLINE:
                            gc_user_decision = GC_UserDecision.UPDATE_OUTLINE
                        case GC_UserDecision.DRAFT_PAPER:
                            gc_user_decision = GC_UserDecision.DRAFT_PAPER
                        case GC_UserDecision.UPDATE_CONTENT:
                            gc_user_decision = GC_UserDecision.UPDATE_CONTENT
                        case GC_UserDecision.DRAFT_NEXT_CONTENT:
                            gc_user_decision = GC_UserDecision.DRAFT_NEXT_CONTENT
                        case GC_UserDecision.EXIT_EARLY:
                            gc_user_decision = GC_UserDecision.EXIT_EARLY

                    _delete_guided_conversation_state(self.conversation_context)
                case GC_ConversationStatus.USER_INITIATED:
                    if result.ai_message is not None:
                        response = result.ai_message
                    else:
                        response = ""
                    gc_conversation_status = GC_ConversationStatus.USER_INITIATED
                case GC_ConversationStatus.USER_RETURNED:
                    if result.ai_message is not None:
                        response = result.ai_message
                    else:
                        response = ""
                    gc_conversation_status = GC_ConversationStatus.USER_RETURNED

        return response, gc_conversation_status, gc_user_decision

    # endregion


#
# region Helpers
#


def _get_guided_conversation_storage_path(context: ConversationContext) -> Path:
    """
    Get the path to the directory for storing guided conversation files.
    """
    path = storage_directory_for_context(context) / "guided-conversation"
    if not path.exists():
        path.mkdir(parents=True)
    return path


def _write_guided_conversation_state(context: ConversationContext, state: dict) -> None:
    """
    Write the state of the guided conversation agent to a file.
    """
    path = _get_guided_conversation_storage_path(context) / "state.json"
    path.write_text(json.dumps(state))


def _read_guided_conversation_state(context: ConversationContext) -> dict | None:
    """
    Read the state of the guided conversation agent from a file.
    """
    path = _get_guided_conversation_storage_path(context) / "state.json"
    if path.exists():
        try:
            json_data = path.read_text()
            return json.loads(json_data)
        except Exception:
            pass
    return None


def _delete_guided_conversation_state(context: ConversationContext) -> None:
    """
    Delete the file containing state of the guided conversation agent.
    """
    path = _get_guided_conversation_storage_path(context) / "state.json"
    if path.exists():
        path.unlink()


# endregion
