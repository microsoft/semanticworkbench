import logging
from typing import TYPE_CHECKING

from semantic_workbench_api_model.workbench_model import (
    ConversationEvent,
    ConversationMessage,
    MessageType,
    NewConversationMessage,
    UpdateParticipant,
)
from semantic_workbench_assistant.assistant_app import (
    AssistantConversationInspectorStateDataModel,
    BaseModelAssistantConfig,
    ConversationContext,
)

from .skills.config import SkillsAgentConfigModel
from .skills.controller import AssistantRegistry

export = [
    SkillsAgentConfigModel,
]

logger = logging.getLogger(__name__)

if TYPE_CHECKING:
    from ..config import AssistantConfigModel


assistant_registry = AssistantRegistry()

#
# region Agent
#


class SkillsAgent:
    """
    An agent for using the skills library to create a skill-based assistant.
    """

    def __init__(
        self,
        config_provider: BaseModelAssistantConfig["AssistantConfigModel"],
    ) -> None:
        self.config_provider = config_provider

    # Core response logic for handling messages (chat or command) in the conversation.
    async def respond_to_conversation(
        self, context: ConversationContext, event: ConversationEvent, message: ConversationMessage
    ) -> None:
        """
        Respond to a conversation message.
        """

        # TODO: pass metadata to the assistant for at least adding the content safety metadata to debug

        # get the assistant configuration
        assistant_config = await self.config_provider.get(context.assistant)

        # TODO: pass metadata to the assistant for at least adding the content safety metadata to debug
        # metadata = {"debug": {"content_safety": event.data.get(content_safety.metadata_key, {})}}

        # update the participant status to indicate the assistant is thinking
        await context.update_participant_me(UpdateParticipant(status="thinking..."))
        try:
            # replace the following with your own logic for processing a message created event
            assistant = await assistant_registry.get_assistant(
                context,
                assistant_config.agents_config.skills_agent.chat_driver_config,
                assistant_config.service_config,
            )
            if assistant:
                await assistant.put_message(message.content)
            else:
                logging.error("Assistant not created")
        except Exception as e:
            logging.exception("exception in on_message_created")
            await context.send_messages(
                NewConversationMessage(
                    message_type=MessageType.note,
                    content=f"Unhandled error: {e}",
                )
            )
        finally:
            # update the participant status to indicate the assistant is done thinking
            await context.update_participant_me(UpdateParticipant(status=None))


# endregion


#
# region Inspector
#


class SkillsAgentConversationInspectorStateProvider:
    display_name = "Skills"
    description = "Inspect the state of the skills agent."

    def __init__(
        self,
        config_provider: BaseModelAssistantConfig["AssistantConfigModel"],
    ) -> None:
        self.config_provider = config_provider

    async def get(self, context: ConversationContext) -> AssistantConversationInspectorStateDataModel:
        """
        Get the artifacts for the conversation.
        """

        # get the configuration for the artifact agent
        config = await self.config_provider.get(context.assistant)
        if not config.agents_config.skills_agent.enabled:
            return AssistantConversationInspectorStateDataModel(
                data={"content": "Skills Agent is disabled in assistant configuration."}
            )

        return AssistantConversationInspectorStateDataModel(
            data={"content": "Skills Agent inspection is not implemented."}
        )


# endregion
