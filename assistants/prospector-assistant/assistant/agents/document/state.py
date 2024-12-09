import json
import logging
from enum import StrEnum
from os import path
from pathlib import Path
from typing import Any

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

from ...config import AssistantConfigModel
from .config import GuidedConversationConfigModel
from .gc_draft_outline_feedback_config import GCDraftOutlineFeedbackConfigModel
from .guided_conversation import GuidedConversation

logger = logging.getLogger(__name__)


#
# region Other ... TBD
#


class Status(StrEnum):
    UNDEFINED = "undefined"
    INITIATED = "initiated"
    NOT_COMPLETED = "not_completed"
    USER_COMPLETED = "user_completed"
    USER_EXIT_EARLY = "user_exit_early"


class GC_ConversationStatus(StrEnum):
    UNDEFINED = "undefined"
    USER_INITIATED = "user_initiated"
    USER_RETURNED = "user_returned"
    USER_COMPLETED = "user_completed"


class GC_UserDecision(StrEnum):
    UNDEFINED = "undefined"
    UPDATE_OUTLINE = "update_outline"
    DRAFT_PAPER = "draft_paper"
    EXIT_EARLY = "exit_early"


# endregion

#
# region Steps
#


class StepName(StrEnum):
    UNDEFINED = "undefined"
    DRAFT_OUTLINE = "step_draft_outline"
    GC_GET_OUTLINE_FEEDBACK = "step_gc_get_outline_feedback"
    FINISH = "step_finish"


class StepStatus(StrEnum):
    UNDEFINED = "undefined"
    INITIATED = "initiated"
    NOT_COMPLETED = "not_completed"
    USER_COMPLETED = "user_completed"
    USER_EXIT_EARLY = "user_exit_early"


class Step(BaseModel):
    name: StepName = StepName.UNDEFINED
    status: StepStatus = StepStatus.UNDEFINED
    data: dict = {"run_count": 0}
    gc_conversation_status: GC_ConversationStatus = GC_ConversationStatus.UNDEFINED
    gc_user_decision: GC_UserDecision = GC_UserDecision.UNDEFINED

    def __init__(self, **data: Any) -> None:
        super().__init__(**data)

        name = data.get("name")
        if name is not None:
            self._error_check()
            match name:
                case StepName.DRAFT_OUTLINE:
                    self._execute = self._step_draft_outline
                case StepName.GC_GET_OUTLINE_FEEDBACK:
                    self._execute = self._step_gc_get_outline_feedback
                case StepName.FINISH:
                    self._execute = self._step_finish
                case _:
                    print(f"{name} mode.")
            logger.info("Document Agent step (%s) initiated: %s", self.get_name())

    async def _execute(
        self,
        attachments_ext: AttachmentsExtension,
        config: AssistantConfigModel,
        context: ConversationContext,
        message: ConversationMessage | None,
        metadata: dict[str, Any] = {},
    ) -> StepStatus:
        status = StepStatus.UNDEFINED
        return status

    def _error_check(self) -> None:
        # name and status should either both be UNDEFINED or both be defined. Always.
        if (self.name is StepName.UNDEFINED and self.status is not Status.UNDEFINED) or (
            self.status is Status.UNDEFINED and self.name is not StepName.UNDEFINED
        ):
            logger.error(
                "Either step name or step status is UNDEFINED, and the other is not. Both must be UNDEFINED at the same time: Step name is %s, status is %s",
                self.name,
                self.status,
            )

        # user decision should be set only if conversation status is completed. otherwise undefined.
        if (
            self.gc_conversation_status is GC_ConversationStatus.UNDEFINED
            and self.gc_user_decision is not GC_UserDecision.UNDEFINED
        ) or (
            self.gc_user_decision is GC_UserDecision.UNDEFINED
            and self.gc_conversation_status is GC_ConversationStatus.USER_COMPLETED
        ):
            logger.error(
                "Either GC conversation status is UNDEFINED, while GC user decision is not. Or GC user decision is UNDEFINED while GC conversation status is COMPLETED. GC conversation status is %s, GC user decision is %s",
                self.gc_conversation_status,
                self.gc_user_decision,
            )

    def reset(self) -> None:
        # TODO: consider if this is the right way to reset a step, fix the # noqa: F841
        self = Step()  # noqa: F841

    def set_name(self, name: StepName) -> None:
        if name is StepName.UNDEFINED:  # need to reset step
            self.reset()
        if name is not self.name:  # update if new step name
            self = Step(name=name, status=StepStatus.NOT_COMPLETED)
        self._error_check()

    def get_name(self) -> StepName:
        self._error_check()
        return self.name

    def set_status(self, status: StepStatus) -> None:
        if status is Status.UNDEFINED:  # need to reset mode
            self.reset()
        self.status = status
        self._error_check()

    def get_status(self) -> StepStatus:
        self._error_check()
        return self.status

    def set_data(self, run_count: int) -> None:
        self.data["run_count"] = run_count

    def get_data(self) -> dict[str, Any]:
        return self.data

    def get_gc_user_decision(self) -> GC_UserDecision:
        self._error_check()
        return self.gc_user_decision

    def get_gc_conversation_status(self) -> GC_ConversationStatus:
        self._error_check()
        return self.gc_conversation_status

    async def _step_draft_outline(
        self,
        attachments_ext: AttachmentsExtension,
        config: AssistantConfigModel,
        context: ConversationContext,
        message: ConversationMessage | None,
        metadata: dict[str, Any] = {},
    ) -> StepStatus:
        logger.info("Document Agent running step: %s", self.get_name())
        method_metadata_key = "_step_draft_outline"

        # get conversation related info -- for now, if no message, assuming no prior conversation
        conversation = None
        participants_list = None
        if message is not None:
            conversation = await context.get_messages(before=message.id)
            if message.message_type == MessageType.chat:
                conversation.messages.append(message)
            participants_list = await context.get_participants(include_inactive=True)

        # get attachments related info
        attachment_messages = await attachments_ext.get_completion_messages_for_attachments(
            context, config=config.agents_config.attachment_agent
        )

        # get outline related info
        outline: str | None = None
        # path = _get_document_agent_conversation_storage_path(context)
        if path.exists(storage_directory_for_context(context) / "document_agent/outline.txt"):
            outline = (storage_directory_for_context(context) / "document_agent/outline.txt").read_text()

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
                completion_args = {
                    "messages": chat_completion_messages,
                    "model": config.request_config.openai_model,
                    "response_format": {"type": "text"},
                }
                completion = await client.chat.completions.create(**completion_args)
                message_content = completion.choices[0].message.content
                _on_success_metadata_update(metadata, method_metadata_key, config, chat_completion_messages, completion)

            except Exception as e:
                logger.exception(f"exception occurred calling openai chat completion: {e}")
                message_content = (
                    "An error occurred while calling the OpenAI API. Is it configured correctly?"
                    "View the debug inspector for more information."
                )
                _on_error_metadata_update(metadata, method_metadata_key, config, chat_completion_messages, e)

        # store only latest version for now (will keep all versions later as need arises)
        (storage_directory_for_context(context) / "document_agent/outline.txt").write_text(message_content)

        # send a command response to the conversation only if from a command. Otherwise return a normal chat message.
        message_type = MessageType.chat
        if message is not None and message.message_type == MessageType.command:
            message_type = MessageType.command

        await context.send_messages(
            NewConversationMessage(
                content=message_content,
                message_type=message_type,
                metadata=metadata,
            )
        )

        return StepStatus.USER_COMPLETED

    async def _step_gc_get_outline_feedback(
        self,
        attachments_ext: AttachmentsExtension,
        config: AssistantConfigModel,
        context: ConversationContext,
        message: ConversationMessage | None,
        metadata: dict[str, Any] = {},
    ) -> StepStatus:
        logger.info("Document Agent running step: %s", self.get_name())
        method_metadata_key = "_step_gc_get_outline_feedback"

        # Initiate Guided Conversation
        gc_outline_feedback_config: GuidedConversationConfigModel = GCDraftOutlineFeedbackConfigModel()
        guided_conversation = GuidedConversation(
            config=config,
            openai_client=openai_client.create_client(config.service_config),
            agent_config=gc_outline_feedback_config,
            conversation_context=context,
        )

        # Update artifact
        conversation_status_str = GC_ConversationStatus.UNDEFINED
        step_data = self.get_data()
        run_count_value = step_data.get("run_count")
        if not isinstance(run_count_value, int):
            logger.error("Document Agent - step run_count not of type int.")
        else:
            match run_count_value:  # could be bool instead. But maybe a run count use later?
                case 0:
                    conversation_status_str = GC_ConversationStatus.USER_INITIATED
                case _:
                    conversation_status_str = GC_ConversationStatus.USER_RETURNED

        filenames = await attachments_ext.get_attachment_filenames(context)
        filenames_str = ", ".join(filenames)

        outline_str: str = ""
        if path.exists(storage_directory_for_context(context) / "document_agent/outline.txt"):
            outline_str = (storage_directory_for_context(context) / "document_agent/outline.txt").read_text()

        artifact_dict = guided_conversation.get_artifact_dict()
        if artifact_dict is not None:
            artifact_dict["conversation_status"] = conversation_status_str
            artifact_dict["filenames"] = filenames_str
            artifact_dict["current_outline"] = outline_str
            guided_conversation.set_artifact_dict(artifact_dict)
        else:
            logger.error("artifact_dict unavailable.")

        # Run conversation step
        step_status = StepStatus.UNDEFINED
        try:
            user_message = None
            if message is not None and self.get_status() is not Status.INITIATED:
                user_message = message.content
                if len(message.filenames) != 0:
                    user_message = user_message + " Newly attached files: " + filenames_str

            (
                response,
                self.gc_conversation_status,
                self.gc_user_decision,
            ) = await guided_conversation.step_conversation(
                last_user_message=user_message,
            )

            # this could get cleaned up
            if self.gc_conversation_status is GC_ConversationStatus.USER_COMPLETED:
                if self.gc_user_decision is GC_UserDecision.EXIT_EARLY:
                    step_status = StepStatus.USER_EXIT_EARLY
                else:
                    step_status = StepStatus.USER_COMPLETED
            else:
                step_status = StepStatus.NOT_COMPLETED

            deepmerge.always_merger.merge(
                metadata,
                {
                    "debug": {
                        f"{method_metadata_key}": {"response": response},
                    }
                },
            )

        except Exception as e:
            logger.exception(f"exception occurred processing guided conversation: {e}")
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

        return step_status

    async def _step_finish(
        self,
        attachments_ext: AttachmentsExtension,
        config: AssistantConfigModel,
        context: ConversationContext,
        message: ConversationMessage | None,
        metadata: dict[str, Any] = {},
    ) -> StepStatus:
        # Can do other things here if necessary
        return StepStatus.USER_COMPLETED


# TO REFACTOR LATER AS ABOVE
#    async def _step_draft_content(
#        self,
#        config: AssistantConfigModel,
#        context: ConversationContext,
#        message: ConversationMessage | None,
#        metadata: dict[str, Any] = {},
#    ) -> tuple[Status, StepName | None]:
#        next_step = None
#
#        # Pre-requisites
#        if self._state is None:
#            logger.error("Document Agent state is None. Returning.")
#            return Status.UNDEFINED, next_step
#
#        step = self._state.mode.get_step()
#        step_name = step.get_name()
#        step_status = step.get_status()
#
#        step_called = StepName.DP_DRAFT_CONTENT
#        if step_name is not step_called or (
#            step_status is not Status.NOT_COMPLETED and step_status is not Status.INITIATED
#        ):
#            logger.error(
#                "Document Agent state step: %s, step called: %s, state step completion status: %s. Resetting Mode.",
#                step_name,
#                step_called,
#                step_status,
#            )
#            self._state.mode.reset()
#            self._write_state(context)
#            return self._state.mode.get_status(), next_step
#
#        # Run
#        logger.info("Document Agent running step: %s", step_name)
#        status, next_step_name = await self._draft_content(config, context, message, metadata)
#        step.set_status(status)
#        self._state.mode.set_step(step)
#        self._write_state(context)
#        return step.get_status(), next_step_name
#
#    # endregion
#
#    #
#    # region language model methods
#    #
#
#    async def _draft_content(
#        self,
#        config: AssistantConfigModel,
#        context: ConversationContext,
#        message: ConversationMessage | None,
#        metadata: dict[str, Any] = {},
#    ) -> tuple[Status, StepName | None]:
#        method_metadata_key = "draft_content"
#
#        # get conversation related info -- for now, if no message, assuming no prior conversation
#        conversation = None
#        participants_list = None
#        if message is not None:
#            conversation = await context.get_messages(before=message.id)
#            if message.message_type == MessageType.chat:
#                conversation.messages.append(message)
#            participants_list = await context.get_participants(include_inactive=True)
#
#        # get attachments related info
#        attachment_messages = await self._attachments_extension.get_completion_messages_for_attachments(
#            context, config=config.agents_config.attachment_agent
#        )
#
#        # create chat completion messages
#        chat_completion_messages: list[ChatCompletionMessageParam] = []
#        chat_completion_messages.append(_draft_content_main_system_message())
#        if conversation is not None and participants_list is not None:
#            chat_completion_messages.append(
#                _chat_history_system_message(conversation.messages, participants_list.participants)
#            )
#        chat_completion_messages.extend(openai_client.convert_from_completion_messages(attachment_messages))
#
#        # get outline related info
#        if path.exists(storage_directory_for_context(context) / "document_agent/outline.txt"):
#            document_outline = (storage_directory_for_context(context) / "document_agent/outline.txt").read_text()
#            if document_outline is not None:
#                chat_completion_messages.append(_outline_system_message(document_outline))
#
#        if path.exists(storage_directory_for_context(context) / "document_agent/content.txt"):
#            document_content = (storage_directory_for_context(context) / "document_agent/content.txt").read_text()
#            if document_content is not None:  # only grabs previously written content, not all yet.
#                chat_completion_messages.append(_content_system_message(document_content))
#
#        # make completion call to openai
#        content: str | None = None
#        async with openai_client.create_client(config.service_config) as client:
#            try:
#                completion_args = {
#                    "messages": chat_completion_messages,
#                    "model": config.request_config.openai_model,
#                    "response_format": {"type": "text"},
#                }
#                completion = await client.chat.completions.create(**completion_args)
#                message_content = completion.choices[0].message.content
#                _on_success_metadata_update(metadata, method_metadata_key, config, chat_completion_messages, completion)
#
#            except Exception as e:
#                logger.exception(f"exception occurred calling openai chat completion: {e}")
#                message_content = (
#                    "An error occurred while calling the OpenAI API. Is it configured correctly?"
#                    "View the debug inspector for more information."
#                )
#                _on_error_metadata_update(metadata, method_metadata_key, config, chat_completion_messages, e)
#
#        if content is not None:
#            # store only latest version for now (will keep all versions later as need arises)
#            (storage_directory_for_context(context) / "document_agent/content.txt").write_text(message_content)
#
#            # send a command response to the conversation only if from a command. Otherwise return a normal chat message.
#            message_type = MessageType.chat
#            if message is not None and message.message_type == MessageType.command:
#                message_type = MessageType.command
#
#            await context.send_messages(
#                NewConversationMessage(
#                    content=message_content,
#                    message_type=message_type,
#                    metadata=metadata,
#                )
#            )
#
#        return Status.USER_COMPLETED, None


# endregion


#
# region Modes
#


class ModeName(StrEnum):
    UNDEFINED = "undefined"
    DRAFT_OUTLINE = "mode_draft_outline"
    DRAFT_PAPER = "mode_draft_paper"


class ModeStatus(StrEnum):
    UNDEFINED = "undefined"
    INITIATED = "initiated"
    NOT_COMPLETED = "not_completed"
    USER_COMPLETED = "user_completed"
    USER_EXIT_EARLY = "user_exit_early"


class Mode(BaseModel):
    name: ModeName = ModeName.UNDEFINED
    status: ModeStatus = ModeStatus.UNDEFINED
    current_step: Step = Step()

    def __init__(self, **data: Any) -> None:
        super().__init__(**data)

        name = data.get("name")
        if name is not None:
            match name:
                case ModeName.DRAFT_OUTLINE:
                    self._init_draft_outline_mode()
                case ModeName.DRAFT_PAPER:
                    print(f"{name} mode not implemented.")
                case _:
                    print(f"{name} mode.")

    def _init_draft_outline_mode(self) -> None:
        self._error_check()

        self.get_next_step = self._draft_outline_mode_get_next_step
        if self.get_status() is ModeStatus.INITIATED:
            self.set_step(self.get_next_step())
        else:
            self.set_step(Step(name=self.get_step().get_name(), status=self.get_step().get_status()))

        logger.info(
            "Document Agent mode initiated. Mode Name: %s, Mode Status: %s, Current Step Name: %s",
            self.get_name(),
            self.get_status(),
            self.get_step().get_name(),
        )
        return

    def _draft_outline_mode_get_next_step(self) -> Step:
        current_step_name = self.get_step().get_name()
        logger.info(
            "Document Agent entered _draft_outline_mode_get_next_step. current_step_name: %s",
            self.get_step().get_name(),
        )

        match current_step_name:
            case StepName.UNDEFINED:
                current_step_name = StepName.DRAFT_OUTLINE
            case StepName.DRAFT_OUTLINE:
                current_step_name = StepName.GC_GET_OUTLINE_FEEDBACK
            case StepName.GC_GET_OUTLINE_FEEDBACK:
                user_decision = self.get_step().get_gc_user_decision()
                if user_decision is not GC_UserDecision.UNDEFINED:
                    match user_decision:
                        case GC_UserDecision.UPDATE_OUTLINE:
                            current_step_name = StepName.DRAFT_OUTLINE
                        case GC_UserDecision.DRAFT_PAPER:
                            current_step_name = StepName.FINISH
                        case GC_UserDecision.EXIT_EARLY:
                            current_step_name = StepName.FINISH
            case StepName.FINISH:
                return Step(name=StepName.UNDEFINED, status=StepStatus.UNDEFINED)

        return Step(name=current_step_name, status=StepStatus.INITIATED)

    def _error_check(self) -> None:
        # name and status should either both be UNDEFINED or both be defined. Always.
        if (self.name is ModeName.UNDEFINED and self.status is not ModeStatus.UNDEFINED) or (
            self.status is ModeStatus.UNDEFINED and self.name is not ModeName.UNDEFINED
        ):
            logger.error(
                "Either mode name or mode status is UNDEFINED, and the other is not. Both must be UNDEFINED at the same time: Mode name is %s, status is %s",
                self.name,
                self.status,
            )

    def reset(self) -> None:
        # TODO: consider if this is the right way to reset a mode, fix the # noqa: F841
        self = Mode()  # noqa: F841

    def set_name(self, name: ModeName) -> None:
        if name is ModeName.UNDEFINED:  # need to reset mode
            self.reset()
        if name is not self.name:  # update if new mode name
            self = Mode(name=name, status=ModeStatus.NOT_COMPLETED)
        self._error_check()

    def get_name(self) -> ModeName:
        self._error_check()
        return self.name

    def set_status(self, status: ModeStatus) -> None:
        if status is ModeStatus.UNDEFINED:  # need to reset mode
            self.reset()
        self.status = status
        self._error_check()

    def get_status(self) -> ModeStatus:
        self._error_check()
        return self.status

    def is_running(self) -> bool:
        if self.status is ModeStatus.NOT_COMPLETED:
            return True
        if self.status is ModeStatus.INITIATED:
            return True
        return False  # UNDEFINED, USER_EXIT_EARLY, USER_COMPLETED

    def set_step(self, step: Step) -> None:
        self.cuurent_step = step

    def get_step(self) -> Step:
        return self.current_step

    def get_next_step(self) -> Step:
        return Step()


# endregion

#
# region State
#


class State(BaseModel):
    mode: Mode = Mode()

    def set_mode(self, mode) -> None:
        self.mode = mode


# endregion

#
# region helper methods
#


@staticmethod
def mode_prerequisite_check(state: State, correct_mode_name: ModeName) -> bool:
    mode_name = state.mode.get_name()
    mode_status = state.mode.get_status()
    if mode_name is not correct_mode_name or (
        mode_status is not Status.NOT_COMPLETED and mode_status is not Status.INITIATED
    ):
        logger.error(
            "Document Agent state mode: %s, mode called: %s, state mode completion status: %s.",
            mode_name,
            correct_mode_name,
            mode_status,
        )
        return False
    return True


@staticmethod
def _get_document_agent_conversation_storage_path(context: ConversationContext, filename: str | None = None) -> Path:
    """
    Get the path to the directory for storing files.
    """
    path = storage_directory_for_context(context) / "document_agent"
    if filename:
        path /= filename
    return path


@staticmethod
def write_document_agent_conversation_state(context: ConversationContext, state_dict: dict) -> None:
    """
    Write the state to a file.
    """
    json_data = json.dumps(state_dict)
    path = _get_document_agent_conversation_storage_path(context)
    if not path.exists():
        path.mkdir(parents=True)
    path = path / "state.json"
    path.write_text(json_data)


@staticmethod
def read_document_agent_conversation_state(context: ConversationContext) -> dict | None:
    """
    Read the state from a file.
    """
    path = _get_document_agent_conversation_storage_path(context, "state.json")
    if path.exists():
        try:
            json_data = path.read_text()
            return json.loads(json_data)
        except Exception:
            pass
    return None


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
    "Following the structure of the outline, create the content for the next (or first) page of the"
    " document - don't try to create the entire document in one pass nor wrap it up too quickly, it will be a"
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
