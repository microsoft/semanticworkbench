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
from .status import Status, StepName

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
    ) -> tuple[str, Status, StepName | None]:
        """
        Step the conversation to the next turn.
        """
        next_step_name = None

        rules = agent_config.rules
        conversation_flow = agent_config.conversation_flow
        context = agent_config.context
        resource_constraint = agent_config.resource_constraint
        artifact = agent_config.get_artifact_model()

        # plug in attachments

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

        # convert information in artifact for Document Agent
        # conversation_status:  # this should relate to result.is_conversation_over
        # final_response:  # replace result.ai_message with final_response if "user_completed"

        final_response: str = ""
        conversation_status: str | None = None
        user_decision: str = ""
        response: str = ""

        # to_json is actually to dict, not to json.
        gc_dict = guided_conversation_agent.to_json()
        artifact_item = gc_dict.get("artifact")
        if artifact_item is not None:
            artifact_item = artifact_item.get("artifact")
            if artifact_item is not None:
                final_response = artifact_item.get("final_response")
                conversation_status = artifact_item.get("conversation_status")
                user_decision = artifact_item.get("user_decision")

        # should be returning str and Status for Document Agent to consume.  Update doc agent logic accordingly.
        status: Status = Status.UNDEFINED
        if conversation_status is not None:
            if conversation_status == "Unanswered":
                if result.ai_message is not None:
                    response = result.ai_message
                else:
                    response = ""
                status = Status.NOT_COMPLETED
            elif conversation_status == "user_completed":
                _delete_guided_conversation_state(conversation_context)
                response = final_response
                if user_decision is None:
                    status = Status.USER_COMPLETED
                else:
                    if user_decision == "update_outline":  # this code is becoming highly coupled fyi to the gc configs
                        status = Status.USER_COMPLETED
                        next_step_name = StepName.DO_DRAFT_OUTLINE
                    elif user_decision == "draft_paper":
                        status = Status.USER_COMPLETED
                        next_step_name = (
                            StepName.DP_DRAFT_CONTENT
                        )  # problem if in draft outline mode... that is supposed to go to DO_FINISH.
                        # coupling is now a problem.  and Need to fix the two locations for setting the branching/flow.
                    else:
                        logger.error("unknown user decision")
            else:
                _delete_guided_conversation_state(conversation_context)
                status = Status.USER_EXIT_EARLY
                response = final_response

        return response, status, next_step_name

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


def _delete_guided_conversation_state(context: ConversationContext) -> None:
    """
    Delete the file containing state of the guided conversation agent.
    """
    path = _get_guided_conversation_storage_path(context, "state.json")
    if path.exists():
        path.unlink()


# endregion
