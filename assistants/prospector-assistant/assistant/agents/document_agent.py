import logging
from os import path
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
from semantic_workbench_assistant.assistant_app import ConversationContext, storage_directory_for_context

from ..config import AssistantConfigModel
from .document.config import GuidedConversationAgentConfigModel
from .document.guided_conversation import GuidedConversationAgent

logger = logging.getLogger(__name__)


#
# region Agent
#
class Step(BaseModel):
    function: Callable | None = None
    is_completed: bool = True  # force logic to set this correctly.


class Mode(BaseModel):
    function: Callable | None = None
    step: Step = Step()
    is_completed: bool = True  # force logic to set this correctly.


class State(BaseModel):
    mode: Mode = Mode()


class DocumentAgent:
    """
    An agent for working on document content: creation, editing, translation, etc.
    """

    ### MAJOR PROBLEM TO FIX
    ### Cannot tie agent state to the class, needs to be tied to the conversation context... otherwise a new agent in a different conversation will be using same state info.
    ### Like how gc state is tied to the conversation context.
    ### Problem for gc state, is that being tied to conversation context, it persists to ANY gc call, even ones later... So need to either remove gc state once a gc convo is done,
    ### or set each state more specifically, so can start a new one per that gc convo, or "rewrite" the state for the new gc convo.

    state: State = State()

    def __init__(self, attachments_extension: AttachmentsExtension) -> None:
        self.attachments_extension = attachments_extension
        self._commands = [self.set_mode_draft_outline]  # self.draft_outline]

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

    async def respond_to_conversation(
        self,
        config: AssistantConfigModel,
        context: ConversationContext,
        message: ConversationMessage,
        metadata: dict[str, Any] = {},
    ) -> bool:
        is_mode_running = False

        # Pre-requisites
        if self.state.mode.function is None or self.state.mode.is_completed:
            logger.warning(
                "Document Agent state mode: %s, state mode completion status: %s",
                "None" if self.state.mode.function is None else self.state.mode.function.__name__,
                self.state.mode.is_completed,
            )
            return is_mode_running

        # Run
        mode = self.state.mode
        match self.state.mode.function:
            case self._mode_draft_outline:
                logger.info(f"Document Agent in mode: {mode.function.__name__}")
                is_mode_running = await mode.function(self, config, context, message, metadata)
            case _:
                logger.error("Document Agent failed to find a corresponding mode.")
                is_mode_running = False

        return is_mode_running

    @classmethod
    def set_mode_draft_outline(
        cls,
        config: AssistantConfigModel,
        context: ConversationContext,
        message: ConversationMessage,
        metadata: dict[str, Any] = {},
    ) -> None:
        # Pre-requisites
        if cls.state.mode.function:
            logger.error(f"Document Agent in mode: {cls.state.mode.function.__name__}. Cannot change modes.")
            return

        # Run
        cls.state.mode.function = cls._mode_draft_outline
        cls.state.mode.is_completed = False

    @classmethod
    async def _mode_draft_outline(
        cls,
        instance,
        config: AssistantConfigModel,
        context: ConversationContext,
        message: ConversationMessage,
        metadata: dict[str, Any] = {},
    ) -> bool:
        mode_running = True

        # Pre-requisites
        if cls.state.mode.function != cls._mode_draft_outline or cls.state.mode.is_completed:
            logger.error(
                "Document Agent state mode: %s, mode called: %s, state mode completion status: %s",
                "None" if cls.state.mode.function is None else cls.state.mode.function.__name__,
                cls._mode_draft_outline.__name__,
                cls.state.mode.is_completed,
            )
            return not mode_running

        # Run
        mode = cls.state.mode
        step = cls.state.mode.step
        if step.function is None:
            logger.info("Document Agent mode (%s) at beginning.", cls._mode_draft_outline.__name__)
            step.function = cls._gc_attachment_check
            step.is_completed = False

        if step.is_completed:  # Logic: what step to do next...
            step.is_completed = False
            match cls.state.mode.step.function:
                case cls._gc_attachment_check:
                    step.function = cls._draft_outline
                case cls._draft_outline:
                    step.function = cls._gc_get_outline_feedback
                case cls._gc_get_outline_feedback:
                    step.function = cls._final_outline
                case cls._final_outline:  # The End. Reset.
                    # This isn't quite right.  upon the last step completeing, everthing should be reset.
                    # We shouldn't have to come back in after we are done with another user message to reset stuff.
                    logger.info(f"Document Agent completing mode: {mode.function.__name__}")
                    mode.function = None
                    mode.is_completed = True
                    step.function = None
                    step.is_completed = True
                    return not mode_running

        # Call step
        logger.info(f"Document Agent running mode.step: {step.function.__name__}")
        step.is_completed = await step.function(instance, config, context, message, metadata)
        logger.info("Document Agent mode.step status: %s", "completed" if step.is_completed else "not completed")
        return mode_running

    ###
    # step functions for _mode_draft_outline.
    ###
    @classmethod
    async def _gc_attachment_check(
        cls,
        instance,
        config: AssistantConfigModel,
        context: ConversationContext,
        message: ConversationMessage,
        metadata: dict[str, Any] = {},
    ) -> bool:
        is_completed = await cls._gc_respond_to_conversation(config, gc_config, message, context, metadata)
        return is_completed

    @classmethod
    async def _draft_outline(
        cls,
        instance,
        config: AssistantConfigModel,
        context: ConversationContext,
        message: ConversationMessage,
        metadata: dict[str, Any] = {},
    ) -> bool:
        is_completed = await cls.draft_outline(instance, config, context, message, metadata)
        return is_completed

    @classmethod
    async def _gc_get_outline_feedback(
        cls,
        instance,
        config: AssistantConfigModel,
        context: ConversationContext,
        message: ConversationMessage,
        metadata: dict[str, Any] = {},
    ) -> bool:
        # pretend completed
        return True

    @classmethod
    async def _final_outline(
        cls,
        instance,
        config: AssistantConfigModel,
        context: ConversationContext,
        message: ConversationMessage,
        metadata: dict[str, Any] = {},
    ) -> bool:
        # pretend completed
        return True

    ####

    @classmethod
    async def _gc_respond_to_conversation(
        cls,
        config: AssistantConfigModel,
        gc_config: GuidedConversationAgentConfigModel,
        message: ConversationMessage,
        context: ConversationContext,
        metadata: dict[str, Any] = {},
    ) -> bool:
        method_metadata_key = "document_agent_gc_response"
        is_conversation_over = False

        try:
            response_message, is_conversation_over = await GuidedConversationAgent.step_conversation(
                config=config,
                openai_client=openai_client.create_client(config.service_config),
                agent_config=gc_config,
                conversation_context=context,
                last_user_message=message.content,
            )
            if is_conversation_over:
                return is_conversation_over  # Do not send the hard-coded response message from gc

            if response_message is None:
                # need to double check this^^ None logic, when it would occur in GC. Make "" for now.
                agent_message = ""
            else:
                agent_message = response_message

            # add the completion to the metadata for debugging
            deepmerge.always_merger.merge(
                metadata,
                {
                    "debug": {
                        f"{method_metadata_key}": {"response": agent_message},
                    }
                },
            )

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

        await context.send_messages(
            NewConversationMessage(
                content=agent_message,
                message_type=MessageType.chat,
                metadata=metadata,
            )
        )

        # Need to add a good way to stop mode if an exception occurs.
        # Also need to update the gc state turn count to 0 (and any thing else that needs to be reset) once conversation is over... or exception occurs?)

        return is_conversation_over

    @classmethod
    async def draft_outline(
        cls,
        instance,
        config: AssistantConfigModel,
        context: ConversationContext,
        message: ConversationMessage,
        metadata: dict[str, Any] = {},
    ) -> bool:
        method_metadata_key = "draft_outline"

        # get conversation related info
        conversation = await context.get_messages(before=message.id)
        if message.message_type == MessageType.chat:
            conversation.messages.append(message)
        participants_list = await context.get_participants(include_inactive=True)

        # get attachments related info
        attachment_messages = await instance.attachments_extension.get_completion_messages_for_attachments(
            context, config=config.agents_config.attachment_agent
        )

        # get outline related info
        outline: str | None = None
        if path.exists(storage_directory_for_context(context) / "outline.txt"):
            outline = (storage_directory_for_context(context) / "outline.txt").read_text()

        # create chat completion messages
        chat_completion_messages: list[ChatCompletionMessageParam] = []
        chat_completion_messages.append(_main_system_message())
        chat_completion_messages.append(
            _chat_history_system_message(conversation.messages, participants_list.participants)
        )
        chat_completion_messages.extend(attachment_messages)
        if outline is not None:
            chat_completion_messages.append(_outline_system_message(outline))

        # make completion call to openai
        async with openai_client.create_client(config.service_config) as client:
            try:
                completion_args = {
                    "messages": chat_completion_messages,
                    "model": config.request_config.openai_model,
                    "response_format": {"type": "text"},
                }
                completion = await client.chat.completions.create(**completion_args)
                content = completion.choices[0].message.content
                _on_success_metadata_update(metadata, method_metadata_key, config, chat_completion_messages, completion)

            except Exception as e:
                logger.exception(f"exception occurred calling openai chat completion: {e}")
                content = (
                    "An error occurred while calling the OpenAI API. Is it configured correctly?"
                    "View the debug inspector for more information."
                )
                _on_error_metadata_update(metadata, method_metadata_key, config, chat_completion_messages, e)

        # store only latest version for now (will keep all versions later as need arises)
        (storage_directory_for_context(context) / "outline.txt").write_text(content)

        # send the response to the conversation only if from a command.  Otherwise return info to caller.
        message_type = MessageType.chat
        if message.message_type == MessageType.command:
            message_type = MessageType.command

        await context.send_messages(
            NewConversationMessage(
                content=content,
                message_type=message_type,
                metadata=metadata,
            )
        )

        return True


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
