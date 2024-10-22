import logging
from enum import Enum
from typing import Any, Callable

import deepmerge
import openai_client
from assistant_extensions.attachments import AttachmentsExtension
from openai.types.chat import (
    ChatCompletionMessageParam,
    ChatCompletionSystemMessageParam,
)
from pydantic import BaseModel
from semantic_workbench_api_model.workbench_model import (
    ConversationMessage,
    ConversationParticipant,
    MessageType,
    NewConversationMessage,
)
from semantic_workbench_assistant.assistant_app import (
    ConversationContext,
)

from ..config import AssistantConfigModel
from .document.guided_conversation import GuidedConversationAgent, GuidedConversationAgentConfigModel

logger = logging.getLogger(__name__)


#
# region Agent
#
class RoutineMode(Enum):
    UNDEFINED = 1
    E2E_DRAFT_OUTLINE = 2  # change name later


class Routine(BaseModel):
    mode: RoutineMode = RoutineMode.UNDEFINED
    step: Callable | None = None


class State(BaseModel):
    routine: Routine = Routine()


class DocumentAgent:
    """
    An agent for working on document content: creation, editing, translation, etc.
    """

    state: State = State()

    def __init__(self, attachments_extension: AttachmentsExtension) -> None:
        self.attachments_extension = attachments_extension
        self._commands = [self.set_draft_outline_mode]  # self.draft_outline]

    @property
    def commands(self) -> list[Callable]:
        return self._commands

    async def receive_command(
        self,
        config: AssistantConfigModel,
        context: ConversationContext,
        message: ConversationMessage,
        metadata: dict[str, Any] = {},
    ) -> None:
        # remove initial "/". This is not intuitive to me.
        msg_command_name = message.command_name
        msg_command_name = msg_command_name.replace("/", "")

        # check if available. If not, ignore for now.
        command_found = False
        for command in self.commands:
            if command.__name__ == msg_command_name:
                logger.info(f"Found command {message.command_name}")
                command_found = True
                command(config, context, message, metadata)  # does not handle command with args or async commands
                break
        if not command_found:
            logger.warning(f"Could not find command {message.command_name}")

    def respond_to_conversation(
        self,
        config: AssistantConfigModel,
        context: ConversationContext,
        message: ConversationMessage,
        metadata: dict[str, Any] = {},
    ) -> None:
        # check state mode
        match self.state.routine.mode:
            case RoutineMode.UNDEFINED:
                logger.info("Document Agent has no routine mode set. Returning.")
                return
            case RoutineMode.E2E_DRAFT_OUTLINE:
                return self._run_e2e_draft_outline()

    @classmethod
    def set_draft_outline_mode(
        cls,
        config: AssistantConfigModel,
        context: ConversationContext,
        message: ConversationMessage,
        metadata: dict[str, Any] = {},
    ) -> None:
        if cls.state.routine.mode is RoutineMode.UNDEFINED:
            cls.state.routine.mode = RoutineMode.E2E_DRAFT_OUTLINE
        else:
            logger.info(
                f"Document Agent in the middle of routine: {cls.state.routine.mode}.  Cannot change routine modes."
            )

    def _run_e2e_draft_outline(self) -> None:
        logger.info("In _run_e2e_draft_outline")
        return

    async def _gc_respond_to_conversation(
        self,
        config: AssistantConfigModel,
        gc_config: GuidedConversationAgentConfigModel,
        context: ConversationContext,
        metadata: dict[str, Any] = {},
    ) -> None:
        method_metadata_key = "document_agent_gc_response"
        is_conversation_over = False
        last_user_message = None

        while not is_conversation_over:
            try:
                response_message, is_conversation_over = await GuidedConversationAgent.step_conversation(
                    config=config,
                    openai_client=openai_client.create_client(config.service_config),
                    agent_config=gc_config,
                    conversation_context=context,
                    last_user_message=last_user_message,
                )
                if response_message is None:
                    # need to double check this^^ None logic, when it would occur in GC. Make "" for now.
                    agent_message = ""
                else:
                    agent_message = response_message

                if not is_conversation_over:
                    # add the completion to the metadata for debugging
                    deepmerge.always_merger.merge(
                        metadata,
                        {
                            "debug": {
                                f"{method_metadata_key}": {"response": agent_message},
                            }
                        },
                    )
                else:
                    break

            except Exception as e:
                logger.exception(f"exception occurred processing guided conversation: {e}")
                agent_message = "An error occurred while processing the guided conversation."
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

            # send the response to the conversation
            await context.send_messages(
                NewConversationMessage(
                    content=agent_message,
                    message_type=MessageType.chat,
                    metadata=metadata,
                )
            )

    # async def draft_outline(
    #    self,
    #    config: AssistantConfigModel,
    #    context: ConversationContext,
    #    message: ConversationMessage,
    #    metadata: dict[str, Any] = {},
    # ) -> tuple[str, dict[str, Any]]:
    #    method_metadata_key = "draft_outline"


#
#    # get conversation related info
#    conversation = await context.get_messages(before=message.id)
#    if message.message_type == MessageType.chat:
#        conversation.messages.append(message)
#    participants_list = await context.get_participants(include_inactive=True)
#
#    # get attachments related info
#    attachment_messages = await self.attachments_extension.get_completion_messages_for_attachments(
#        context, config=config.agents_config.attachment_agent
#    )
#
#    # get outline related info
#    outline: str | None = None
#    if path.exists(storage_directory_for_context(context) / "outline.txt"):
#        outline = (storage_directory_for_context(context) / "outline.txt").read_text()
#
#    # create chat completion messages
#    chat_completion_messages: list[ChatCompletionMessageParam] = []
#    chat_completion_messages.append(_main_system_message())
#    chat_completion_messages.append(
#        _chat_history_system_message(conversation.messages, participants_list.participants)
#    )
#    chat_completion_messages.extend(attachment_messages)
#    if outline is not None:
#        chat_completion_messages.append(_outline_system_message(outline))
#
#    # make completion call to openai
#    async with openai_client.create_client(config.service_config) as client:
#        try:
#            completion_args = {
#                "messages": chat_completion_messages,
#                "model": config.request_config.openai_model,
#                "response_format": {"type": "text"},
#            }
#            completion = await client.chat.completions.create(**completion_args)
#            content = completion.choices[0].message.content
#            _on_success_metadata_update(metadata, method_metadata_key, config, chat_completion_messages, completion)
#
#        except Exception as e:
#            logger.exception(f"exception occurred calling openai chat completion: {e}")
#            content = (
#                "An error occurred while calling the OpenAI API. Is it configured correctly?"
#                "View the debug inspector for more information."
#            )
#            _on_error_metadata_update(metadata, method_metadata_key, config, chat_completion_messages, e)
#
#    # store only latest version for now (will keep all versions later as need arises)
#    (storage_directory_for_context(context) / "outline.txt").write_text(content)
#
#    # send the response to the conversation only if from a command.  Otherwise return info to caller.
#    message_type = MessageType.chat
#    if message.message_type == MessageType.command:
#        message_type = MessageType.command
#
#    await context.send_messages(
#        NewConversationMessage(
#            content=content,
#            message_type=message_type,
#            metadata=metadata,
#        )
#    )
#
#    return content, metadata


# endregion


#
# region Inspector
#


# class DocumentAgentConversationInspectorStateProvider:
#    display_name = "Guided Conversation"
#    description = "State of the guided conversation feature within the conversation."
#
#    def __init__(
#        self,
#        config_provider: BaseModelAssistantConfig["AssistantConfigModel"],
#    ) -> None:
#        self.config_provider = config_provider
#
#    async def get(self, context: ConversationContext) -> AssistantConversationInspectorStateDataModel:
#        """
#        Get the state for the conversation.
#        """
#
#        state = _read_guided_conversation_state(context)
#
#        return AssistantConversationInspectorStateDataModel(data=state or {"content": "No state available."})
#
#
## endregion


#
# region Message Helpers
#


def _main_system_message() -> ChatCompletionSystemMessageParam:
    message: ChatCompletionSystemMessageParam = {"role": "system", "content": draft_outline_main_system_message}
    return message


def _chat_history_system_message(
    conversation_messages: list[ConversationMessage],
    participants: list[ConversationParticipant],
) -> ChatCompletionSystemMessageParam:
    chat_history_message_list = []
    for conversation_message in conversation_messages:
        chat_history_message = _format_message(conversation_message, participants)
        chat_history_message_list.append(chat_history_message)
    chat_history_str = " ".join(chat_history_message_list)

    message: ChatCompletionSystemMessageParam = {
        "role": "system",
        "content": f"<CONVERSATION>{chat_history_str}</CONVERSATION>",
    }
    return message


def _outline_system_message(outline: str) -> ChatCompletionSystemMessageParam:
    if outline is not None:
        message: ChatCompletionSystemMessageParam = {
            "role": "system",
            "content": (f"<EXISTING_OUTLINE>{outline}</EXISTING_OUTLINE>"),
        }
    return message


draft_outline_main_system_message = (
    "Generate an outline for the document, including title. The outline should include the key points that will"
    " be covered in the document. If attachments exist, consider the attachments and the rationale for why they"
    " were uploaded. Consider the conversation that has taken place. If a prior version of the outline exists,"
    " consider the prior outline. The new outline should be a hierarchical structure with multiple levels of"
    " detail, and it should be clear and easy to understand. The outline should be generated in a way that is"
    " consistent with the document that will be generated from it. Do not include any explanation before or after"
    " the outline, as the generated outline will be stored as its own document."
)
# ("You are an AI assistant that helps draft outlines for a future flushed-out document."
# " You use information from a chat history between a user and an assistant, a prior version of a draft"
# " outline if it exists, as well as any other attachments provided by the user to inform a newly revised "
# "outline draft. Provide ONLY any outline. Provide no further instructions to the user.")


def _on_success_metadata_update(
    metadata: dict[str, Any],
    method_metadata_key: str,
    config: AssistantConfigModel,
    chat_completion_messages: list[ChatCompletionMessageParam],
    completion: Any,
) -> None:
    deepmerge.always_merger.merge(
        metadata,
        {
            "debug": {
                f"{method_metadata_key}": {
                    "request": {
                        "model": config.request_config.openai_model,
                        "messages": openai_client.truncate_messages_for_logging(chat_completion_messages),
                        "max_tokens": config.request_config.response_tokens,
                    },
                    "response": completion.model_dump() if completion else "[no response from openai]",
                },
            }
        },
    )


def _on_error_metadata_update(
    metadata: dict[str, Any],
    method_metadata_key: str,
    config: AssistantConfigModel,
    chat_completion_messages: list[ChatCompletionMessageParam],
    e: Exception,
) -> None:
    deepmerge.always_merger.merge(
        metadata,
        {
            "debug": {
                f"{method_metadata_key}": {
                    "request": {
                        "model": config.request_config.openai_model,
                        "messages": openai_client.truncate_messages_for_logging(chat_completion_messages),
                    },
                    "error": str(e),
                },
            }
        },
    )


# endregion


#
# borrowed temporarily from Prospector chat.py
#


def _format_message(message: ConversationMessage, participants: list[ConversationParticipant]) -> str:
    """
    Format a conversation message for display.
    """
    conversation_participant = next(
        (participant for participant in participants if participant.id == message.sender.participant_id),
        None,
    )
    participant_name = conversation_participant.name if conversation_participant else "unknown"
    message_datetime = message.timestamp.strftime("%Y-%m-%d %H:%M:%S")
    return f"[{participant_name} - {message_datetime}]: {message.content}"


# endregion

#
# region GC agent config temp
#
# pull in GC config with its defaults, and then make changes locally here for now.
gc_config = GuidedConversationAgentConfigModel()


# endregion


##### FROM NOTEBOOK
# await document_skill.draft_outline(context=unused, openai_client=async_client, model=model)
#
# decision, user_feedback = await document_skill.get_user_feedback(
#                                context=unused, openai_client=async_client, model=model, outline=True
#                            )
#
# while decision == "[ITERATE]":
# await document_skill.draft_outline(
#                                context=unused, openai_client=async_client, model=model, user_feedback=user_feedback
#                            )
# decision, user_feedback = await document_skill.get_user_feedback(
#                                context=unused, openai_client=async_client, model=model, outline=True
#                            )
