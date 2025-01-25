import logging
from abc import abstractmethod
from enum import StrEnum
from os import path
from pathlib import Path
from typing import Any, Protocol

import deepmerge
import openai_client
from assistant.agents.document import gc_draft_content_feedback_config, gc_draft_outline_feedback_config
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

from ...config import AssistantConfigModel
from .guided_conversation import GC_ConversationStatus, GC_UserDecision, GuidedConversation

logger = logging.getLogger(__name__)

#
# region Steps
#


class StepName(StrEnum):
    DRAFT_OUTLINE = "step_draft_outline"
    GC_GET_OUTLINE_FEEDBACK = "step_gc_get_outline_feedback"
    DRAFT_CONTENT = "step_draft_content"
    GC_GET_CONTENT_FEEDBACK = "step_gc_get_content_feedback"
    FINISH = "step_finish"


class StepStatus(StrEnum):
    NOT_COMPLETED = "not_completed"
    USER_COMPLETED = "user_completed"
    USER_EXIT_EARLY = "user_exit_early"


class StepProtocol(Protocol):
    @abstractmethod
    async def execute(
        self,
        run_count: int,
        attachments_ext: AttachmentsExtension,
        config: AssistantConfigModel,
        context: ConversationContext,
        message: ConversationMessage | None,
        metadata: dict[str, Any] = {},
    ) -> tuple[StepStatus, GC_UserDecision]: ...


class StepDraftOutline(StepProtocol):
    async def execute(
        self,
        run_count: int,
        attachments_ext: AttachmentsExtension,
        config: AssistantConfigModel,
        context: ConversationContext,
        message: ConversationMessage | None,
        metadata: dict[str, Any] = {},
    ) -> tuple[StepStatus, GC_UserDecision]:
        method_metadata_key = "_step_draft_outline"

        # get conversation related info -- for now, if no message, assuming no prior conversation
        participants_list = await context.get_participants(include_inactive=True)
        if message is not None:
            conversation = await context.get_messages(before=message.id)
            if message.message_type == MessageType.chat:
                conversation.messages.append(message)
        else:
            conversation = await context.get_messages()

        # get attachments related info
        attachment_messages = await attachments_ext.get_completion_messages_for_attachments(
            context, config=config.agents_config.attachment_agent
        )

        # get outline related info
        outline = read_document_outline(context)

        # create chat completion messages
        chat_completion_messages: list[ChatCompletionMessageParam] = []
        chat_completion_messages.append(_draft_outline_main_system_message())
        if conversation is not None and participants_list is not None:
            chat_completion_messages.append(
                _chat_history_system_message(conversation.messages, participants_list.participants)
            )
        chat_completion_messages.extend(openai_client.convert_from_completion_messages(attachment_messages))
        if outline is not None:
            chat_completion_messages.append(_outline_system_message(outline))

        # make completion call to openai
        async with openai_client.create_client(config.service_config) as client:
            try:
                completion = await client.chat.completions.create(
                    messages=chat_completion_messages,
                    model=config.request_config.openai_model,
                    response_format={"type": "text"},
                )
                new_outline = completion.choices[0].message.content
                _on_success_metadata_update(metadata, method_metadata_key, config, chat_completion_messages, completion)

            except Exception as e:
                logger.exception("Document Agent State: Exception occurred calling openai chat completion")
                new_outline = (
                    "An error occurred while calling the OpenAI API. Is it configured correctly?"
                    "View the debug inspector for more information."
                )
                _on_error_metadata_update(metadata, method_metadata_key, config, chat_completion_messages, e)

        # store only latest version for now (will keep all versions later as need arises)
        if new_outline is not None:
            write_document_outline(context, new_outline)

            # send a command response to the conversation only if from a command. Otherwise return a normal chat message.
            message_type = MessageType.chat
            if message is not None and message.message_type == MessageType.command:
                message_type = MessageType.command

            await context.send_messages(
                NewConversationMessage(
                    content=new_outline,
                    message_type=message_type,
                    metadata=metadata,
                )
            )

        return StepStatus.USER_COMPLETED, GC_UserDecision.UNDEFINED


class StepGetOutlineFeedback(StepProtocol):
    async def execute(
        self,
        run_count: int,
        attachments_ext: AttachmentsExtension,
        config: AssistantConfigModel,
        context: ConversationContext,
        message: ConversationMessage | None,
        metadata: dict[str, Any] = {},
    ) -> tuple[StepStatus, GC_UserDecision]:
        method_metadata_key = "_step_gc_get_outline_feedback"

        # Update artifact
        conversation_status_str = GC_ConversationStatus.USER_INITIATED
        if run_count > 0:
            conversation_status_str = GC_ConversationStatus.USER_RETURNED

        filenames = await attachments_ext.get_attachment_filenames(context)
        filenames_str = ", ".join(filenames)

        outline_str = read_document_outline(context) or ""
        artifact_updates = {
            "conversation_status": conversation_status_str,
            "filenames": filenames_str,
            "current_outline": outline_str,
        }

        # Initiate Guided Conversation
        guided_conversation = GuidedConversation(
            config=config,
            openai_client=openai_client.create_client(config.service_config),
            agent_config=gc_draft_outline_feedback_config.config,
            artifact_model=gc_draft_outline_feedback_config.ArtifactModel,
            conversation_context=context,
            artifact_updates=artifact_updates,
        )

        step_status = StepStatus.NOT_COMPLETED
        gc_conversation_status = GC_ConversationStatus.UNDEFINED
        gc_user_decision = GC_UserDecision.UNDEFINED

        # Run conversation step
        try:
            user_message = None
            if message is not None:
                user_message = message.content
                if len(message.filenames) != 0:
                    user_message = user_message + " Newly attached files: " + filenames_str

            (
                response,
                gc_conversation_status,
                gc_user_decision,
            ) = await guided_conversation.step_conversation(
                last_user_message=user_message,
            )

            # this could get cleaned up
            if gc_conversation_status is GC_ConversationStatus.USER_COMPLETED:
                step_status = StepStatus.USER_COMPLETED
                if gc_user_decision is GC_UserDecision.EXIT_EARLY:
                    step_status = StepStatus.USER_EXIT_EARLY

            # need to update gc state artifact?

            deepmerge.always_merger.merge(
                metadata,
                {
                    "debug": {
                        f"{method_metadata_key}": guided_conversation.guided_conversation_agent.to_json(),
                    }
                },
            )

        except Exception as e:
            logger.exception(f"Document Agent State: Exception occurred processing guided conversation: {e}")
            response = "An error occurred while processing the guided conversation."
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
                content=response,
                message_type=MessageType.chat,
                metadata=metadata,
            )
        )

        return step_status, gc_user_decision


class StepDraftContent(StepProtocol):
    async def execute(
        self,
        run_count: int,
        attachments_ext: AttachmentsExtension,
        config: AssistantConfigModel,
        context: ConversationContext,
        message: ConversationMessage | None,
        metadata: dict[str, Any] = {},
    ) -> tuple[StepStatus, GC_UserDecision]:
        method_metadata_key = "_step_draft_content"

        # get conversation related info -- for now, if no message, assuming no prior conversation
        participants_list = await context.get_participants(include_inactive=True)
        if message is not None:
            conversation = await context.get_messages(before=message.id)
            if message.message_type == MessageType.chat:
                conversation.messages.append(message)
        else:
            conversation = await context.get_messages()

        # get attachments related info
        attachment_messages = await attachments_ext.get_completion_messages_for_attachments(
            context, config=config.agents_config.attachment_agent
        )

        # create chat completion messages
        chat_completion_messages: list[ChatCompletionMessageParam] = []
        chat_completion_messages.append(_draft_content_main_system_message())
        if conversation is not None and participants_list is not None:
            chat_completion_messages.append(
                _chat_history_system_message(conversation.messages, participants_list.participants)
            )
        chat_completion_messages.extend(openai_client.convert_from_completion_messages(attachment_messages))

        # get outline related info
        if path.exists(storage_directory_for_context(context) / "document_agent/outline.txt"):
            document_outline = (storage_directory_for_context(context) / "document_agent/outline.txt").read_text()
            if document_outline is not None:
                chat_completion_messages.append(_outline_system_message(document_outline))

        document_content = read_document_content(context)
        if document_content is not None:  # only grabs previously written content, not all yet.
            chat_completion_messages.append(_content_system_message(document_content))

        # make completion call to openai
        content: str | None = None
        async with openai_client.create_client(config.service_config) as client:
            try:
                completion = await client.chat.completions.create(
                    messages=chat_completion_messages,
                    model=config.request_config.openai_model,
                    response_format={"type": "text"},
                )
                content = completion.choices[0].message.content
                _on_success_metadata_update(metadata, method_metadata_key, config, chat_completion_messages, completion)

            except Exception as e:
                logger.exception(f"Document Agent State: Exception occurred calling openai chat completion: {e}")
                content = (
                    "An error occurred while calling the OpenAI API. Is it configured correctly?"
                    "View the debug inspector for more information."
                )
                _on_error_metadata_update(metadata, method_metadata_key, config, chat_completion_messages, e)

        if content is not None:
            # store only latest version for now (will keep all versions later as need arises)
            write_document_content(context, content)

            # send a command response to the conversation only if from a command. Otherwise return a normal chat message.
            message_type = MessageType.chat
            if message is not None and message.message_type == MessageType.command:
                message_type = MessageType.command

            await context.send_messages(
                NewConversationMessage(
                    content=content,
                    message_type=message_type,
                    metadata=metadata,
                )
            )

        return StepStatus.USER_COMPLETED, GC_UserDecision.UNDEFINED


class StepGetContentFeedback(StepProtocol):
    async def execute(
        self,
        run_count: int,
        attachments_ext: AttachmentsExtension,
        config: AssistantConfigModel,
        context: ConversationContext,
        message: ConversationMessage | None,
        metadata: dict[str, Any] = {},
    ) -> tuple[StepStatus, GC_UserDecision]:
        method_metadata_key = "_step_gc_get_content_feedback"

        # Update artifact
        conversation_status_str = GC_ConversationStatus.USER_INITIATED
        if run_count > 0:
            conversation_status_str = GC_ConversationStatus.USER_RETURNED

        filenames = await attachments_ext.get_attachment_filenames(context)
        filenames_str = ", ".join(filenames)

        outline_str = read_document_outline(context) or ""
        content_str = read_document_content(context) or ""

        artifact_updates = {
            "conversation_status": conversation_status_str,
            "filenames": filenames_str,
            "approved_outline": outline_str,
            "current_content": content_str,
        }

        # Initiate Guided Conversation
        guided_conversation = GuidedConversation(
            config=config,
            openai_client=openai_client.create_client(config.service_config),
            agent_config=gc_draft_content_feedback_config.config,
            artifact_model=gc_draft_content_feedback_config.ArtifactModel,
            conversation_context=context,
            artifact_updates=artifact_updates,
        )

        step_status = StepStatus.NOT_COMPLETED
        gc_conversation_status = GC_ConversationStatus.UNDEFINED
        gc_user_decision = GC_UserDecision.UNDEFINED

        # Run conversation step
        try:
            user_message = None
            if message is not None:
                user_message = message.content
                # if len(message.filenames) != 0:  # Not sure we want to support this right now for content/page
                #    user_message = user_message + " Newly attached files: " + filenames_str

            (
                response,
                gc_conversation_status,
                gc_user_decision,
            ) = await guided_conversation.step_conversation(
                last_user_message=user_message,
            )

            # this could get cleaned up
            if gc_conversation_status is GC_ConversationStatus.USER_COMPLETED:
                step_status = StepStatus.USER_COMPLETED
                if gc_user_decision is GC_UserDecision.EXIT_EARLY:
                    step_status = StepStatus.USER_EXIT_EARLY

            # need to update gc state artifact?

            deepmerge.always_merger.merge(
                metadata,
                {
                    "debug": {
                        f"{method_metadata_key}": {"response": response},
                    }
                },
            )

        except Exception as e:
            logger.exception(f"Document Agent State: Exception occurred processing guided conversation: {e}")
            response = "An error occurred while processing the guided conversation."
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
                content=response,
                message_type=MessageType.chat,
                metadata=metadata,
            )
        )

        return step_status, gc_user_decision


class StepFinish(StepProtocol):
    async def execute(
        self,
        run_count: int,
        attachments_ext: AttachmentsExtension,
        config: AssistantConfigModel,
        context: ConversationContext,
        message: ConversationMessage | None,
        metadata: dict[str, Any] = {},
    ) -> tuple[StepStatus, GC_UserDecision]:
        # Can do other things here if necessary
        return StepStatus.USER_COMPLETED, GC_UserDecision.UNDEFINED


# endregion


#
# region Modes
#


class ModeName(StrEnum):
    DRAFT_OUTLINE = "mode_draft_outline"
    DRAFT_PAPER = "mode_draft_paper"


class ModeStatus(StrEnum):
    INITIATED = "initiated"
    NOT_COMPLETED = "not_completed"
    USER_COMPLETED = "user_completed"
    USER_EXIT_EARLY = "user_exit_early"


# endregion


#
# region State
#


class State(BaseModel):
    step_run_count: dict[str, int] = {}
    mode_name: ModeName = ModeName.DRAFT_OUTLINE
    mode_status: ModeStatus = ModeStatus.INITIATED
    current_step_name: StepName = StepName.DRAFT_OUTLINE
    current_step_status: StepStatus = StepStatus.NOT_COMPLETED


# endregion

#
# region helper methods
#


def _get_document_agent_conversation_storage_path(context: ConversationContext) -> Path:
    """
    Get the path to the directory for storing files.
    """
    path = storage_directory_for_context(context) / "document_agent"
    if not path.exists():
        path.mkdir(parents=True)

    return path


def write_document_agent_conversation_state(context: ConversationContext, state: State) -> None:
    """
    Write the state to a file.
    """
    path = _get_document_agent_conversation_storage_path(context)
    path = path / "state.json"
    path.write_text(state.model_dump_json())


def read_document_agent_conversation_state(context: ConversationContext) -> State:
    """
    Read the state from a file.
    """
    path = _get_document_agent_conversation_storage_path(context) / "state.json"
    if path.exists():
        try:
            json_data = path.read_text()
            return State.model_validate_json(json_data)
        except Exception:
            pass

    return State()


def read_document_outline(context: ConversationContext) -> str | None:
    """
    Read the outline from a file.
    """
    path = _get_document_agent_conversation_storage_path(context) / "outline.txt"
    if not path.exists():
        return None

    return path.read_text()


def write_document_outline(context: ConversationContext, outline: str) -> None:
    """
    Write the outline to a file.
    """
    path = _get_document_agent_conversation_storage_path(context) / "outline.txt"
    path.write_text(outline)


def read_document_content(context: ConversationContext) -> str | None:
    """
    Read the content from a file.
    """
    path = _get_document_agent_conversation_storage_path(context) / "content.txt"
    if not path.exists():
        return None

    return path.read_text()


def write_document_content(context: ConversationContext, content: str) -> None:
    """
    Write the content to a file.
    """
    path = _get_document_agent_conversation_storage_path(context) / "content.txt"
    path.write_text(content)


@staticmethod
def _draft_outline_main_system_message() -> ChatCompletionSystemMessageParam:
    message: ChatCompletionSystemMessageParam = {"role": "system", "content": draft_outline_main_system_message}
    return message


@staticmethod
def _draft_content_main_system_message() -> ChatCompletionSystemMessageParam:
    message: ChatCompletionSystemMessageParam = {
        "role": "system",
        "content": draft_content_continue_main_system_message,
    }
    return message


@staticmethod
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


@staticmethod
def _outline_system_message(outline: str) -> ChatCompletionSystemMessageParam:
    message: ChatCompletionSystemMessageParam = {
        "role": "system",
        "content": (f"<EXISTING_OUTLINE>{outline}</EXISTING_OUTLINE>"),
    }
    return message


@staticmethod
def _content_system_message(content: str) -> ChatCompletionSystemMessageParam:
    message: ChatCompletionSystemMessageParam = {
        "role": "system",
        "content": (f"<EXISTING_CONTENT>{content}</EXISTING_CONTENT>"),
    }
    return message


draft_outline_main_system_message = (
    "Generate an outline for the document, including title. The outline should include the key points that will"
    " be covered in the document. If attachments exist, consider the attachments and the rationale for why they"
    " were uploaded. Consider the conversation that has taken place. If a prior version of the outline exists,"
    " consider the prior outline. The new outline should be a hierarchical structure with multiple levels of"
    " detail, and it should be clear and easy to understand. The outline should be generated in a way that is"
    " consistent with the document that will be generated from it. Do not include any explanation before or after"
    " the outline, as the generated outline will be stored as its own document. The generated outline should use Markdown."
)
# ("You are an AI assistant that helps draft outlines for a future flushed-out document."
# " You use information from a chat history between a user and an assistant, a prior version of a draft"
# " outline if it exists, as well as any other attachments provided by the user to inform a newly revised "
# "outline draft. Provide ONLY any outline. Provide no further instructions to the user.")

draft_content_continue_main_system_message = (
    "Following the structure of the provided outline, create the content for the next page of the"
    " document. If there is no existing content supplied, start with the beginning of the provided outline to create the first page of content."
    " Don't try to create the entire document in one pass nor wrap it up too quickly, it will be a"
    " multi-page document so just create the next page. It's more important to maintain"
    " an appropriately useful level of detail. After this page is generated, the system will follow up"
    " and ask for the next page. If you have already generated all the pages for the"
    " document as defined in the outline, return empty content."
)
# ("You are an AI assistant that helps draft new content of a document based on an outline."
# " You use information from a chat history between a user and an assistant, the approved outline from the user,"
# "and an existing version of drafted content if it exists, as well as any other attachments provided by the user to inform newly revised "
# "content. Newly drafted content does not need to cover the entire outline.  Instead it should be limited to a reasonable 100 lines of natural language"
# " or subsection of the outline (which ever is shorter). The newly drafted content should be written as to append to any existing drafted content."
# " This way the user can review newly drafted content as a subset of the future full document and not be overwhelmed."
# "Only provide the newly drafted content. Provide no further instructions to the user.")

draft_content_iterate_main_system_message = (
    "Following the structure of the outline, iterate on the currently drafted page of the"
    " document. It's more important to maintain"
    " an appropriately useful level of detail. After this page is iterated upon, the system will follow up"
    " and ask for the next page."
)


@staticmethod
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
                        "messages": chat_completion_messages,
                        "max_tokens": config.request_config.response_tokens,
                    },
                    "response": completion.model_dump() if completion else "[no response from openai]",
                },
            }
        },
    )


@staticmethod
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
                        "messages": chat_completion_messages,
                    },
                    "error": str(e),
                },
            }
        },
    )


# borrowed from Prospector chat.py
@staticmethod
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
