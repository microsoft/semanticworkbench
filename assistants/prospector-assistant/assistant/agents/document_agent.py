import json
import logging
from enum import StrEnum
from os import path
from pathlib import Path
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
class StepEnum(StrEnum):
    DO_GC_ATTACHMENT_CHECK = "step_gc_attachment_check"
    DO_DRAFT_OUTLINE = "step_draft_outline"
    DO_GC_GET_OUTLINE_FEEDBACK = "step_gc_get_outline_feedback"
    DO_FINAL_OUTLINE = "step_final_outline"


class ModeEnum(StrEnum):
    DRAFT_OUTLINE = "mode_draft_outline"


class Step(BaseModel):
    name: StepEnum | None = None
    is_completed: bool = True  # force logic to set this correctly.


class Mode(BaseModel):
    name: ModeEnum | None = None
    step_order: list[StepEnum] = []
    current_step: Step = Step()
    is_completed: bool = True  # force logic to set this correctly.


class State(BaseModel):
    mode: Mode = Mode()


class DocumentAgent:
    """
    An agent for working on document content: creation, editing, translation, etc.
    """

    def __init__(self, attachments_extension: AttachmentsExtension) -> None:
        self.attachments_extension = attachments_extension
        self._commands = [self.set_mode_draft_outline]
        self._mode_to_method: dict[ModeEnum, Callable] = {
            ModeEnum.DRAFT_OUTLINE: self._mode_draft_outline,
        }
        self._step_to_method: dict[StepEnum, Callable] = {
            StepEnum.DO_GC_ATTACHMENT_CHECK: self._step_gc_attachment_check,
            StepEnum.DO_DRAFT_OUTLINE: self._step_draft_outline,
            StepEnum.DO_GC_GET_OUTLINE_FEEDBACK: self._step_gc_get_outline_feedback,
            StepEnum.DO_FINAL_OUTLINE: self._step_final_outline,
        }

    @property
    def commands(self) -> list[Callable]:
        return self._commands

    def get_mode_method(self, mode: ModeEnum | None) -> Callable | None:
        if mode is None:
            return None
        return self._mode_to_method.get(mode)

    def get_step_method(self, step: StepEnum | None) -> Callable | None:
        if step is None:
            return None
        return self._step_to_method.get(step)

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
        # Retrieve Document Agent conversation state
        state = _get_state(context)
        mode_name = _get_mode_name(state)

        # Pre-requisites
        # Document Agent must already be in a mode (for now).
        if mode_name is None:
            logger.warning("Document Agent must be in a mode to respond. Current state mode: None")
            return _is_mode_running(state)

        # Run
        match mode_name:
            case ModeEnum.DRAFT_OUTLINE:
                mode_method = self.get_mode_method(ModeEnum.DRAFT_OUTLINE)
                if mode_method:
                    logger.info(f"Document Agent in mode: {ModeEnum.DRAFT_OUTLINE}")
                    mode_completed = await mode_method(config, context, message, metadata)
                    if mode_completed:
                        _reset_mode(state)
                else:
                    logger.error("Document Agent failed to find a corresponding mode method.")
                    _reset_mode(state)
            case _:
                logger.error("Document Agent failed to find a corresponding mode.")
                _reset_mode(state)

        return _is_mode_running(state)

    def set_mode_draft_outline(
        self,
        config: AssistantConfigModel,
        context: ConversationContext,
        message: ConversationMessage,
        metadata: dict[str, Any] = {},
    ) -> None:
        # Retrieve Document Agent conversation state
        state = _get_state(context)
        mode_name = _get_mode_name(state)

        # Pre-requisites
        # Document Agent cannot already be in a mode(for now).
        if mode_name:
            logger.warning("Document Agent already in mode: %s. Cannot change modes.", mode_name)
            return

        # Run
        _set_mode_name(state, ModeEnum.DRAFT_OUTLINE)
        _set_mode_completed(state, False)

        # Update Document Agent conversation state
        _set_state(context, state)

    # endregion

    #
    # region mode and step methods
    #

    # For somewhere... will need to handle scenario that a step is considered "complete", but it is due to the user wanting to exit.
    # This is particularly true for GC steps. This may involve needing to change some of the GC code return values to understand
    # "WHY" the gc is considered complete.  This is valid for any of the steps.  So a RESULT (of a results reason enum) or something like that.
    # not just a boolean for if completed or not.

    async def _mode_draft_outline(
        self,
        config: AssistantConfigModel,
        context: ConversationContext,
        message: ConversationMessage,
        metadata: dict[str, Any] = {},
    ) -> bool:
        # Retrieve Document Agent conversation state
        state = _get_state(context)
        mode_name = _get_mode_name(state)
        is_completed = _get_mode_completed(state)

        # Pre-requisites
        # We can't be here if the mode doesn't match (or is complete).  This needs to be updated prior.
        if mode_name is not ModeEnum.DRAFT_OUTLINE or is_completed:
            logger.error(
                "Document Agent state mode: %s, mode called: %s, state mode completion status: %s",
                "None" if mode_name is None else mode_name,
                ModeEnum.DRAFT_OUTLINE,
                is_completed,
            )
            _set_mode_completed(state, True)
            _set_state(context, state)
            return _get_mode_completed(state)

        # Setup - Would like to do this earlier/separately at some point... here for now
        _set_mode_steps(
            state,
            [
                StepEnum.DO_GC_ATTACHMENT_CHECK,
                StepEnum.DO_DRAFT_OUTLINE,
                StepEnum.DO_GC_GET_OUTLINE_FEEDBACK,
                StepEnum.DO_FINAL_OUTLINE,
            ],
        )
        _set_state(context, state)

        # Run
        current_step_name = _get_current_step_name(state)
        if current_step_name is None:
            logger.info("Document Agent mode (%s) at beginning.", ModeEnum.DRAFT_OUTLINE)
            _set_current_step_name(state, _get_mode_steps(state)[0])
            _set_state(context, state)
            current_step_name = _get_current_step_name(state)

        step_method = self.get_step_method(current_step_name)
        if step_method:
            await step_method(state, config, context, message, metadata)  # calls next step if needed and update state.
        else:
            logger.error("Document Agent failed to find a corresponding step method.")
            _set_mode_completed(state, True)
            _set_state(context, state)

        # Final step is complete -- RESET
        final_step_name = _get_final_step_name(state)
        current_step_name = _get_current_step_name(state)
        is_current_step_completed = _get_current_step_completed(state)
        if current_step_name is final_step_name and is_current_step_completed:
            logger.info("Document Agent completing mode: %s", ModeEnum.DRAFT_OUTLINE)
            _reset_mode(state)
            _set_state(context, state)

        # Right now a lot of control at each step layer to update the state... not sure if we want this. e.g.
        # _step_gc_get_outline_feedback just returns.  It is not updating state to say it is completed, so we keep
        # coming back to it.  This is correct if we expect each state to correctly update the state.
        # if we don't want each step to have that control, and it needs to be done at the mode level, this could get
        # more interesting, since the completion of one step will call the next step, and on, until it bubbles back up to
        # the mode level.  a different solution )kind of what I had), was that each step needs to return and the mode
        # function needs to maintain the logic of checking for that steps completion and calling the next step...  the
        # problem with this is we don't know how many immediate "completions" of steps might occur in a row.  This second approach
        # only works if we assume the next step call will have at least one "incompletion" to respond with.  We could use a while loop,
        # and perhaps that would work... since right now its kind of recursive.  at any incompletion, it would stop and wait for user input
        # the mode level would just have to make sure to update to the correct current step so that the next user input
        # gets routed to the correct function call.

        ### TRY THIS MONDAY -- use a while loop instead of a recursive approach for a series of step completions...
        #
        return _get_mode_completed(state)

    async def _call_next_step(
        self,
        state: State,
        config: AssistantConfigModel,
        context: ConversationContext,
        message: ConversationMessage,
        metadata: dict[str, Any] = {},
    ) -> None:
        next_step_name = _get_next_step_name(state)
        if next_step_name is None:
            return

        next_step_method = self.get_step_method(next_step_name)
        _set_current_step_name(state, next_step_name)
        _set_state(context, state)

        if next_step_method:
            await next_step_method(state, config, context, message, metadata)
        else:
            logger.error("Document Agent failed to find a corresponding next step method.")
            _set_mode_completed(state, True)  # For right now, we bail.
            _set_state(context, state)

    async def _step_gc_attachment_check(
        self,
        state: State,
        config: AssistantConfigModel,
        context: ConversationContext,
        message: ConversationMessage,
        metadata: dict[str, Any] = {},
    ) -> None:
        # Pre-requisites
        current_step_name = _get_current_step_name(state)
        is_completed = _get_current_step_completed(state)

        if current_step_name is not StepEnum.DO_GC_ATTACHMENT_CHECK or is_completed:
            logger.error(
                "Document Agent state step: %s, step called: %s, state step completion status: %s",
                "None" if current_step_name is None else current_step_name,
                StepEnum.DO_GC_ATTACHMENT_CHECK,
                is_completed,
            )
            _reset_mode(state)  # For right now, we bail.
            _set_state(context, state)

        logger.info(f"Document Agent running current step: {StepEnum.DO_GC_ATTACHMENT_CHECK}")

        # Run
        is_completed = await self._gc_respond_to_conversation(config, gc_config, message, context, metadata)
        _set_current_step_completed(state, is_completed)
        _set_state(context, state)

        if is_completed:
            await self._call_next_step(state, config, context, message, metadata)

    async def _step_draft_outline(
        self,
        state: State,
        config: AssistantConfigModel,
        context: ConversationContext,
        message: ConversationMessage,
        metadata: dict[str, Any] = {},
    ) -> None:
        # Pre-requisites
        current_step_name = _get_current_step_name(state)
        is_completed = _get_current_step_completed(state)

        if current_step_name is not StepEnum.DO_DRAFT_OUTLINE or is_completed:
            logger.error(
                "Document Agent state step: %s, step called: %s, state step completion status: %s",
                "None" if current_step_name is None else current_step_name,
                StepEnum.DO_DRAFT_OUTLINE,
                is_completed,
            )
            _reset_mode(state)  # For right now, we bail.
            _set_state(context, state)

        logger.info(f"Document Agent running current step: {StepEnum.DO_DRAFT_OUTLINE}")

        # Run
        is_completed = await self._draft_outline(config, context, message, metadata)
        _set_current_step_completed(state, is_completed)
        _set_state(context, state)

        if is_completed:
            await self._call_next_step(state, config, context, message, metadata)

    async def _step_gc_get_outline_feedback(
        self,
        state: State,
        config: AssistantConfigModel,
        context: ConversationContext,
        message: ConversationMessage,
        metadata: dict[str, Any] = {},
    ) -> None:
        # pretend completed
        return

    async def _step_final_outline(
        self,
        state: State,
        config: AssistantConfigModel,
        context: ConversationContext,
        message: ConversationMessage,
        metadata: dict[str, Any] = {},
    ) -> None:
        # pretend completed
        return

    # endregion

    #
    # region language model methods
    #

    async def _gc_respond_to_conversation(
        self,
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

    async def _draft_outline(
        self,
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
        attachment_messages = await self.attachments_extension.get_completion_messages_for_attachments(
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
# region Helpers
#
def _reset_mode(state: State) -> None:
    state.mode.name = None
    state.mode.is_completed = True
    state.mode.current_step = Step()
    state.mode.step_order = []


def _set_mode_name(state: State, name: ModeEnum | None) -> None:
    # update if setting to a new mode
    if name is not state.mode.name:
        state.mode.name = name
        state.mode.is_completed = False
        state.mode.current_step = Step()
        state.mode.step_order = []
    # reset mode if setting to a None
    if name is None:
        _reset_mode(state)


def _get_mode_name(state: State) -> ModeEnum | None:
    if state.mode.name is None:
        state.mode.is_completed = True  # None should always be set to completed
    return state.mode.name


def _set_mode_completed(state: State, status: bool) -> None:
    state.mode.is_completed = status

    if state.mode.name is None:
        state.mode.is_completed = True  # None should always be set to completed


def _get_mode_completed(state: State) -> bool:
    return state.mode.is_completed


def _is_mode_running(state: State) -> bool:
    # This is such a pain right now.  Higher level wants to know if mode is running or not...
    # But this level it seems more natural to ask if mode is completed or not.  Using this
    # helper until we decide on best approach.  (Don't want to track two separate variables that
    # should always be inverses of one another.)
    if state.mode.is_completed:
        return False
    return True


def _set_mode_steps(state: State, steps: list[StepEnum]) -> None:
    state.mode.step_order = steps


def _get_mode_steps(state: State) -> list[StepEnum]:
    return state.mode.step_order


def _set_current_step_name(state: State, name: StepEnum | None) -> None:
    # reset is_completed if setting to a new step
    if name is not state.mode.current_step.name:
        state.mode.current_step.name = name
        state.mode.current_step.is_completed = False
    if name is None:
        state.mode.current_step.is_completed = True


def _get_current_step_name(state: State) -> StepEnum | None:
    if state.mode.current_step.name is None:
        state.mode.current_step.is_completed = True  # None should always be set to completed
    return state.mode.current_step.name


def _get_next_step_name(state: State) -> StepEnum | None:
    current_step_name = state.mode.current_step.name
    steps = state.mode.step_order

    if len(steps) == 0:
        return None

    if current_step_name is steps[-1]:
        return None

    for index, step in enumerate(steps[:-1]):
        if step is current_step_name:
            return steps[index + 1]


def _get_final_step_name(state: State) -> StepEnum | None:
    steps = state.mode.step_order
    if len(steps) == 0:
        return None
    return steps[-1]


def _set_current_step_completed(state: State, status: bool) -> None:
    state.mode.current_step.is_completed = status
    if state.mode.current_step.name is None:
        state.mode.current_step.is_completed = True  # None should always be set to completed


def _get_current_step_completed(state: State) -> bool:
    return state.mode.current_step.is_completed


def _get_state(context: ConversationContext) -> State:
    state_dict = _read_document_agent_conversation_state(context)
    if state_dict is not None:
        state = State(**state_dict)
    else:
        logger.info("Document Agent: no state found. Creating new state.")
        state = State()
    return state


def _set_state(context: ConversationContext, state: State) -> None:
    _write_document_agent_conversation_state(context, state.model_dump())


def _get_document_agent_conversation_storage_path(context: ConversationContext, filename: str | None = None) -> Path:
    """
    Get the path to the directory for storing files.
    """
    path = storage_directory_for_context(context) / "document_agent"
    if filename:
        path /= filename
    return path


def _write_document_agent_conversation_state(context: ConversationContext, state: dict) -> None:
    """
    Write the state to a file.
    """
    json_data = json.dumps(state)
    path = _get_document_agent_conversation_storage_path(context)
    if not path.exists():
        path.mkdir(parents=True)
    path = path / "state.json"
    path.write_text(json_data)


def _read_document_agent_conversation_state(context: ConversationContext) -> dict | None:
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

    #


# borrowed from Prospector chat.py
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
