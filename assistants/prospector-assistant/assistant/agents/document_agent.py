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
from .document.config import GuidedConversationConfigModel
from .document.gc_attachment_check_config import GCAttachmentCheckConfigModel
from .document.gc_draft_outline_feedback_config import GCDraftOutlineFeedbackConfigModel
from .document.guided_conversation import GuidedConversation
from .document.status import Status, StepName

logger = logging.getLogger(__name__)


#
# region state, mode, and steps
#


class ModeName(StrEnum):
    UNDEFINED = "undefined"
    DRAFT_OUTLINE = "mode_draft_outline"
    DRAFT_PAPER = "mode_draft_paper"


class Step(BaseModel):
    name: StepName = StepName.UNDEFINED
    status: Status = Status.UNDEFINED

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
        # should this throw an exception?

    def reset(self) -> None:
        # TODO: consider if this is the right way to reset a step, fix the # noqa: F841
        self = Step()  # noqa: F841

    def set_name(self, name: StepName) -> None:
        if name is StepName.UNDEFINED:  # need to reset step
            self.reset()
        if name is not self.name:  # update if new step name
            self = Step(name=name, status=Status.NOT_COMPLETED)
        self._error_check()

    def get_name(self) -> StepName:
        self._error_check()
        return self.name

    def set_status(self, status: Status) -> None:
        if status is Status.UNDEFINED:  # need to reset mode
            self.reset()
        self.status = status
        self._error_check()

    def get_status(self) -> Status:
        self._error_check()
        return self.status


class Mode(BaseModel):
    name: ModeName = ModeName.UNDEFINED
    status: Status = Status.UNDEFINED
    step: Step = Step()
    step_order: list[dict[str, StepName | int]] = [{}]

    def _error_check(self) -> None:
        # name and status should either both be UNDEFINED or both be defined. Always.
        if (self.name is ModeName.UNDEFINED and self.status is not Status.UNDEFINED) or (
            self.status is Status.UNDEFINED and self.name is not ModeName.UNDEFINED
        ):
            logger.error(
                "Either mode name or mode status is UNDEFINED, and the other is not. Both must be UNDEFINED at the same time: Mode name is %s, status is %s",
                self.name,
                self.status,
            )
        # should this throw an exception?

    def reset(self) -> None:
        # TODO: consider if this is the right way to reset a mode, fix the # noqa: F841
        self = Mode()  # noqa: F841

    def set_name(self, name: ModeName) -> None:
        if name is ModeName.UNDEFINED:  # need to reset mode
            self.reset()
        if name is not self.name:  # update if new mode name
            self = Mode(name=name, status=Status.NOT_COMPLETED)
        self._error_check()

    def get_name(self) -> ModeName:
        self._error_check()
        return self.name

    def set_status(self, status: Status) -> None:
        if status is Status.UNDEFINED:  # need to reset mode
            self.reset()
        self.status = status
        self._error_check()

    def get_status(self) -> Status:
        self._error_check()
        return self.status

    def is_running(self) -> bool:
        if self.status is Status.NOT_COMPLETED:
            return True
        if self.status is Status.INITIATED:
            return True
        return False  # UNDEFINED, USER_EXIT_EARLY, USER_COMPLETED

    def set_step(self, step: Step) -> None:
        self.step = step

    def get_step(self) -> Step:
        return self.step

    def set_step_order(self, steps: list[dict[str, StepName | int]]) -> None:
        self.step_order = steps

    def get_step_order(self) -> list[dict[str, StepName | int]]:
        return self.step_order

    def get_next_step(self) -> Step | None:
        steps = self.step_order
        if len(steps) == 0:
            return None

        # logic below is repetitive... needs clean up
        step = self.get_step()
        step_name = step.get_name()
        current_step_name = steps[-1].get("step_name")
        if isinstance(current_step_name, StepName):
            if current_step_name is step_name:
                return None  # on final step
        else:
            logger.error("step_name is not StepName instance")
            next_step_name = StepName.UNDEFINED
            status = Status.UNDEFINED
            return Step(name=next_step_name, status=status)

        next_step_name = StepName.UNDEFINED
        status = Status.UNDEFINED
        for index, step in enumerate(steps[:-1]):
            current_step_name = step.get("step_name")
            if isinstance(current_step_name, StepName):
                if current_step_name is step_name:
                    next_step_name = steps[index + 1].get("step_name")
                    if isinstance(next_step_name, StepName):
                        status = Status.INITIATED
                        break
                    else:
                        logger.error("step_name not found in step of step_list")
                        next_step_name = StepName.UNDEFINED
                        status = Status.UNDEFINED
                        break
            else:
                logger.error("step_name is not StepName instance")
                break

        return Step(name=next_step_name, status=status)


class State(BaseModel):
    mode: Mode = Mode()

    def set_mode(self, mode) -> None:
        self.mode = mode


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
def _write_document_agent_conversation_state(context: ConversationContext, state_dict: dict) -> None:
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


# endregion

#
# region document agent
#


class DocumentAgent:
    """
    An agent for working on document content: creation, editing, translation, etc.
    """

    def __init__(self, attachments_extension: AttachmentsExtension) -> None:
        self._attachments_extension: AttachmentsExtension = attachments_extension
        self._state: State | None = None
        self._commands: list[Callable] = [self._set_mode_draft_outline, self._set_mode_draft_paper]
        self._mode_name_to_method: dict[ModeName, Callable] = {
            ModeName.DRAFT_OUTLINE: self._mode_draft_outline,
            ModeName.DRAFT_PAPER: self._mode_draft_paper,
        }
        self._step_name_to_method: dict[StepName, Callable] = {}  # To be defined in mode method

    @property
    def commands(self) -> list[Callable]:
        return self._commands

    def _write_state(self, context: ConversationContext) -> None:
        if self._state is None:
            logger.error("Document Agent: local state is None. Cannot write to storage.")
            return
        _write_document_agent_conversation_state(context, self._state.model_dump())

    def _read_state(self, context: ConversationContext) -> State:
        state_dict = _read_document_agent_conversation_state(context)
        if state_dict is not None:
            state = State(**state_dict)
        else:
            logger.info("Document Agent: no state found in storage. Returning a new state.")
            state = State()
        return state

    def _get_mode_method(self, mode: Mode | None) -> Callable | None:
        if mode is None or mode.name is ModeName.UNDEFINED:
            return None
        return self._mode_name_to_method.get(mode.name)

    def _get_step_method(self, step: Step | None) -> Callable | None:
        if step is None or step.name is StepName.UNDEFINED:
            return None
        return self._step_name_to_method.get(step.name)

    # Not currently used
    async def receive_command(
        self,
        config: AssistantConfigModel,
        context: ConversationContext,
        message: ConversationMessage,
        metadata: dict[str, Any] = {},
    ) -> None:
        self._state = self._read_state(context)

        # remove initial "/". This is not intuitive to me.
        msg_command_name = message.command_name
        msg_command_name = msg_command_name.replace("/", "")

        # check if available. If not, ignore for now.
        command_found = False
        for command in self.commands:
            if command.__name__ == msg_command_name:
                logger.info("Found command %s", message.command_name)
                command_found = True
                command(config, context, message, metadata)  # does not handle command with args or async commands
                break
        if not command_found:
            logger.warning("Could not find command %s", message.command_name)

    def _set_mode_draft_outline(
        self,
        config: AssistantConfigModel,
        context: ConversationContext,
        message: ConversationMessage | None,
        metadata: dict[str, Any] = {},
    ) -> None:
        # Pre-requisites
        if self._state is None:
            logger.error("Document Agent state is None. Returning.")
            return

        mode = self._state.mode
        if mode.is_running():
            logger.warning("Document Agent already in mode: %s. Cannot change modes.", mode.get_name())
            return

        # Run
        self._state.mode = Mode(name=ModeName.DRAFT_OUTLINE, status=Status.INITIATED)
        self._write_state(context)

    # Not currently used
    def _set_mode_draft_paper(
        self,
        config: AssistantConfigModel,
        context: ConversationContext,
        message: ConversationMessage | None,
        metadata: dict[str, Any] = {},
    ) -> None:
        # Pre-requisites
        if self._state is None:
            logger.error("Document Agent state is None. Returning.")
            return

        mode = self._state.mode
        if mode.is_running():
            logger.warning("Document Agent already in mode: %s. Cannot change modes.", mode.get_name())
            return

        # Run
        self._state.mode = Mode(name=ModeName.DRAFT_PAPER, status=Status.INITIATED)
        self._write_state(context)

    async def create_document(
        self,
        config: AssistantConfigModel,
        context: ConversationContext,
        message: ConversationMessage | None,
        metadata: dict[str, Any] = {},
    ) -> bool:
        self._state = self._read_state(context)

        # Pre-requisites
        if self._state is None:
            logger.error("Document Agent state is None. Returning.")
            return False

        mode = self._state.mode
        current_mode_name = mode.get_name()
        correct_mode_name = ModeName.DRAFT_OUTLINE  # Will update
        if not mode.is_running():
            self._set_mode_draft_outline(
                config, context, message, metadata
            )  # Will update this mode as implementation expands to full document.
        elif current_mode_name is not correct_mode_name:
            logger.warning(
                "Document Agent not in correct mode. Returning. Current mode: %s Correct mode: %s",
                current_mode_name,
                correct_mode_name,
            )
            return mode.is_running()

        # Run
        mode = self._state.mode
        logger.info("Document Agent in mode %s", mode.get_name())
        mode_method = self._get_mode_method(mode)
        if mode_method:
            mode_status = await mode_method(config, context, message, metadata)
            self._state.mode.set_status(mode_status)
            if mode_status is Status.UNDEFINED:
                logger.error(
                    "Calling corresponding mode method for %s resulted in status %s. Resetting mode.",
                    mode.get_name(),
                    mode_status,
                )
                self._state.mode.reset()
        else:
            logger.error(
                "Document Agent failed to find a corresponding mode method for %s. Resetting mode.", mode.get_name()
            )
            self._state.mode.reset()

        # Update Document Agent conversation state
        self._write_state(context)
        return self._state.mode.is_running()

    # endregion

    #
    # region mode and step methods
    #
    async def _run_mode(
        self,
        config: AssistantConfigModel,
        context: ConversationContext,
        message: ConversationMessage | None,
        metadata: dict[str, Any] = {},
    ) -> Status:
        # Pre-requisites
        if self._state is None:
            logger.error("Document Agent state is None. Returning.")
            return Status.UNDEFINED

        # Run
        mode = self._state.mode
        mode_name = mode.get_name()

        step = self._state.mode.get_step()
        step_name = step.get_name()
        step_status = step.get_status()

        while step_status is Status.INITIATED or step_status is Status.NOT_COMPLETED:
            step_method = self._get_step_method(step)
            if step_method:
                logger.info("Document Agent in step: %s", step_name)
                step_status, next_step_name = await step_method(config, context, message, metadata)

                # Update run_count of step (This will need to be simplified--moved into its own function)
                step_list = self._state.mode.get_step_order()
                for step in step_list:
                    list_step_name = step.get("step_name")
                    if isinstance(list_step_name, StepName):
                        if list_step_name is step_name:
                            # This is bad... "run_count" and "step_name" dependent on implementation in a different function.  Need to cleanup.
                            step_run_count = step.get("run_count")
                            if isinstance(step_run_count, int):
                                step_run_count += 1
                                step["run_count"] = step_run_count
                                self._state.mode.set_step_order(step_list)
                                break  # done
                            else:
                                logger.error(
                                    "Document Agent - step %s in step order does run_count not of type int.", step_name
                                )
                                self._state.mode.reset()
                                self._write_state(context)
                                return self._state.mode.get_status()  # problem
                        else:
                            # End of list
                            if step is step_list[-1]:
                                logger.error("Document Agent - step %s not found in step order.", step_name)
                                self._state.mode.reset()
                                self._write_state(context)
                                return self._state.mode.get_status()  # problem
                    else:
                        logger.error("Document Agent - step_name of wrong type")
                        self._state.mode.reset()
                        self._write_state(context)
                        return self._state.mode.get_status()  # problem

                match step_status:  # resulting status of step_method()
                    case Status.NOT_COMPLETED:
                        self._state.mode.get_step().set_status(step_status)
                        self._state.mode.set_status(step_status)
                        break  # ok - get more user input

                    case Status.USER_COMPLETED:
                        if next_step_name is not None:
                            step = Step(name=next_step_name, status=Status.INITIATED)
                            step_name = step.get_name()
                            step_status = step.get_status()
                            self._state.mode.set_step(step)
                            self._write_state(context)
                            continue  # ok - don't need user input yet
                        else:  # go with prescribed order?  Not sure if we want this long term, or just go with above
                            next_step = self._state.mode.get_next_step()
                            if next_step is not None:
                                step = next_step
                                step_name = next_step.get_name()
                                step_status = next_step.get_status()  # new step is Status.INITIATED
                                self._state.mode.set_step(next_step)
                                self._write_state(context)
                                continue  # ok - don't need user input yet
                            else:
                                self._state.mode.get_step().set_status(step_status)
                                self._state.mode.set_status(step_status)
                                break  # ok - all done :)

                    case Status.USER_EXIT_EARLY:
                        self._state.mode.get_step().set_status(step_status)
                        self._state.mode.set_status(step_status)
                        break  # ok - done early :)

                    case _:  # UNDEFINED, INITIATED
                        logger.error(
                            "Document Agent: Calling corresponding step method for %s resulted in status %s. Resetting mode %s.",
                            step_name,
                            step_status,
                            mode_name,
                        )
                        self._state.mode.reset()
                        break  # problem
            else:
                logger.error(
                    "Document Agent failed to find a corresponding step method for %s. Resetting mode %s.",
                    step_name,
                    mode_name,
                )
                self._state.mode.reset()
                break

        # Update Document Agent conversation state
        self._write_state(context)
        return self._state.mode.get_status()

    async def _mode_draft_outline(
        self,
        config: AssistantConfigModel,
        context: ConversationContext,
        message: ConversationMessage | None,
        metadata: dict[str, Any] = {},
    ) -> Status:
        # Pre-requisites
        if self._state is None:
            logger.error("Document Agent state is None. Returning.")
            return Status.UNDEFINED

        mode = self._state.mode
        mode_name = mode.get_name()
        mode_status = mode.get_status()

        if mode_name is not ModeName.DRAFT_OUTLINE or (
            mode_status is not Status.NOT_COMPLETED and mode_status is not Status.INITIATED
        ):
            logger.error(
                "Document Agent state mode: %s, mode called: %s, state mode completion status: %s. Resetting Mode.",
                mode_name,
                ModeName.DRAFT_OUTLINE,
                mode_status,
            )
            self._state.mode.reset()
            self._write_state(context)
            return self._state.mode.get_status()

        # Setup on first run.
        if mode_status is Status.INITIATED:
            self._state.mode.set_step_order(
                [
                    {"step_name": StepName.DO_GC_ATTACHMENT_CHECK, "run_count": 0},
                    {"step_name": StepName.DO_DRAFT_OUTLINE, "run_count": 0},
                    {"step_name": StepName.DO_GC_GET_OUTLINE_FEEDBACK, "run_count": 0},
                    {"step_name": StepName.DO_FINISH, "run_count": 0},
                ],
            )
            logger.info("Document Agent mode (%s) at beginning.", mode_name)
            first_step_name = self._state.mode.get_step_order()[0].get("step_name")
            if not isinstance(first_step_name, StepName):
                logger.error("Document Agent: StepName could not be found in Mode's step order.")
                self._state.mode.reset()
                return self._state.mode.get_status()
            self._state.mode.set_step(Step(name=first_step_name, status=Status.INITIATED))
            self._write_state(context)

        self._step_name_to_method: dict[StepName, Callable] = {
            StepName.DO_GC_ATTACHMENT_CHECK: self._step_gc_attachment_check,
            StepName.DO_DRAFT_OUTLINE: self._step_draft_outline,
            StepName.DO_GC_GET_OUTLINE_FEEDBACK: self._step_gc_get_outline_feedback,
            StepName.DO_FINISH: self._step_finish,
        }

        # Run
        return await self._run_mode(config, context, message, metadata)

    async def _mode_draft_paper(
        self,
        config: AssistantConfigModel,
        context: ConversationContext,
        message: ConversationMessage | None,
        metadata: dict[str, Any] = {},
    ) -> Status:
        # Pre-requisites
        if self._state is None:
            logger.error("Document Agent state is None. Returning.")
            return Status.UNDEFINED

        mode = self._state.mode
        mode_name = mode.get_name()
        mode_status = mode.get_status()

        if mode_name is not ModeName.DRAFT_PAPER or (
            mode_status is not Status.NOT_COMPLETED and mode_status is not Status.INITIATED
        ):
            logger.error(
                "Document Agent state mode: %s, mode called: %s, state mode completion status: %s. Resetting Mode.",
                mode_name,
                ModeName.DRAFT_PAPER,
                mode_status,
            )
            self._state.mode.reset()
            self._write_state(context)
            return self._state.mode.get_status()

        # Setup on first run.
        if mode_status is Status.INITIATED:
            self._state.mode.set_step_order(
                [
                    {"step_name": StepName.DO_GC_ATTACHMENT_CHECK, "run_count": 0},
                    {"step_name": StepName.DO_DRAFT_OUTLINE, "run_count": 0},
                    {"step_name": StepName.DO_GC_GET_OUTLINE_FEEDBACK, "run_count": 0},
                    {"step_name": StepName.DP_DRAFT_CONTENT, "run_count": 0},
                ],
            )
            logger.info("Document Agent mode (%s) at beginning.", mode_name)
            first_step_name = self._state.mode.get_step_order()[0].get("step_name")
            if not isinstance(first_step_name, StepName):
                logger.error("Document Agent: StepName could not be found in Mode's step order.")
                self._state.mode.reset()
                return self._state.mode.get_status()
            self._state.mode.set_step(Step(name=first_step_name, status=Status.INITIATED))
            self._write_state(context)

        self._step_name_to_method: dict[StepName, Callable] = {
            StepName.DO_GC_ATTACHMENT_CHECK: self._step_gc_attachment_check,
            StepName.DO_DRAFT_OUTLINE: self._step_draft_outline,
            StepName.DO_GC_GET_OUTLINE_FEEDBACK: self._step_gc_get_outline_feedback,
            StepName.DP_DRAFT_CONTENT: self._step_draft_content,
        }

        # Run
        return await self._run_mode(config, context, message, metadata)

    async def _step_gc_attachment_check(
        self,
        config: AssistantConfigModel,
        context: ConversationContext,
        message: ConversationMessage | None,
        metadata: dict[str, Any] = {},
    ) -> tuple[Status, StepName | None]:
        next_step = None

        # Pre-requisites
        if self._state is None:
            logger.error("Document Agent state is None. Returning.")
            return Status.UNDEFINED, next_step

        step = self._state.mode.get_step()
        step_name = step.get_name()
        step_status = step.get_status()

        # Pre-requisites
        step_called = StepName.DO_GC_ATTACHMENT_CHECK
        if step_name is not step_called or (
            step_status is not Status.NOT_COMPLETED and step_status is not Status.INITIATED
        ):
            logger.error(
                "Document Agent state step: %s, step called: %s, state step completion status: %s. Resetting Mode.",
                step_name,
                step_called,
                step_status,
            )
            self._state.mode.reset()
            self._write_state(context)
            return self._state.mode.get_status(), next_step

        # Run
        logger.info("Document Agent running step: %s", step_name)
        status, next_step_name = await self._gc_attachment_check(config, context, message, metadata)
        step.set_status(status)
        self._state.mode.set_step(step)
        self._write_state(context)
        return step.get_status(), next_step_name

    async def _step_draft_outline(
        self,
        config: AssistantConfigModel,
        context: ConversationContext,
        message: ConversationMessage | None,
        metadata: dict[str, Any] = {},
    ) -> tuple[Status, StepName | None]:
        next_step = None

        # Pre-requisites
        if self._state is None:
            logger.error("Document Agent state is None. Returning.")
            return Status.UNDEFINED, next_step

        step = self._state.mode.get_step()
        step_name = step.get_name()
        step_status = step.get_status()

        step_called = StepName.DO_DRAFT_OUTLINE
        if step_name is not step_called or (
            step_status is not Status.NOT_COMPLETED and step_status is not Status.INITIATED
        ):
            logger.error(
                "Document Agent state step: %s, step called: %s, state step completion status: %s. Resetting Mode.",
                step_name,
                step_called,
                step_status,
            )
            self._state.mode.reset()
            self._write_state(context)
            return self._state.mode.get_status(), next_step

        # Run
        logger.info("Document Agent running step: %s", step_name)
        status, next_step_name = await self._draft_outline(config, context, message, metadata)
        step.set_status(status)
        self._state.mode.set_step(step)
        self._write_state(context)
        return step.get_status(), next_step_name

    async def _step_gc_get_outline_feedback(
        self,
        config: AssistantConfigModel,
        context: ConversationContext,
        message: ConversationMessage | None,
        metadata: dict[str, Any] = {},
    ) -> tuple[Status, StepName | None]:
        next_step_name = None

        # Pre-requisites
        if self._state is None:
            logger.error("Document Agent state is None. Returning.")
            return Status.UNDEFINED, next_step_name

        step = self._state.mode.get_step()
        step_name = step.get_name()
        step_status = step.get_status()

        # Pre-requisites
        step_called = StepName.DO_GC_GET_OUTLINE_FEEDBACK
        if step_name is not step_called or (
            step_status is not Status.NOT_COMPLETED and step_status is not Status.INITIATED
        ):
            logger.error(
                "Document Agent state step: %s, step called: %s, state step completion status: %s. Resetting Mode.",
                step_name,
                step_called,
                step_status,
            )
            self._state.mode.reset()
            self._write_state(context)
            return self._state.mode.get_status(), next_step_name

        # Run
        user_message: ConversationMessage | None
        if step_status is Status.INITIATED:
            user_message = None
        else:
            user_message = message

        logger.info("Document Agent running step: %s", step_name)
        status, next_step_name = await self._gc_outline_feedback(config, context, user_message, metadata)

        step.set_status(status)
        self._state.mode.set_step(step)
        self._write_state(context)
        return step.get_status(), next_step_name

    async def _step_finish(
        self,
        config: AssistantConfigModel,
        context: ConversationContext,
        message: ConversationMessage | None,
        metadata: dict[str, Any] = {},
    ) -> tuple[Status, StepName | None]:
        # pretend completed
        return Status.USER_COMPLETED, None

    async def _step_draft_content(
        self,
        config: AssistantConfigModel,
        context: ConversationContext,
        message: ConversationMessage | None,
        metadata: dict[str, Any] = {},
    ) -> tuple[Status, StepName | None]:
        next_step = None

        # Pre-requisites
        if self._state is None:
            logger.error("Document Agent state is None. Returning.")
            return Status.UNDEFINED, next_step

        step = self._state.mode.get_step()
        step_name = step.get_name()
        step_status = step.get_status()

        step_called = StepName.DP_DRAFT_CONTENT
        if step_name is not step_called or (
            step_status is not Status.NOT_COMPLETED and step_status is not Status.INITIATED
        ):
            logger.error(
                "Document Agent state step: %s, step called: %s, state step completion status: %s. Resetting Mode.",
                step_name,
                step_called,
                step_status,
            )
            self._state.mode.reset()
            self._write_state(context)
            return self._state.mode.get_status(), next_step

        # Run
        logger.info("Document Agent running step: %s", step_name)
        status, next_step_name = await self._draft_content(config, context, message, metadata)
        step.set_status(status)
        self._state.mode.set_step(step)
        self._write_state(context)
        return step.get_status(), next_step_name

    # endregion

    #
    # region language model methods
    #

    async def _gc_attachment_check(
        self,
        config: AssistantConfigModel,
        context: ConversationContext,
        message: ConversationMessage | None,
        metadata: dict[str, Any] = {},
    ) -> tuple[Status, StepName | None]:
        method_metadata_key = "document_agent_gc_attachment_check"

        gc_attachment_conversation_config: GuidedConversationConfigModel = GCAttachmentCheckConfigModel()

        guided_conversation = GuidedConversation(
            config=config,
            openai_client=openai_client.create_client(config.service_config),
            agent_config=gc_attachment_conversation_config,
            conversation_context=context,
        )

        # update artifact
        filenames = await self._attachments_extension.get_attachment_filenames(context)
        filenames_str = ", ".join(filenames)

        artifact_dict = guided_conversation.get_artifact_dict()
        if artifact_dict is not None:
            artifact_dict["filenames"] = filenames_str
            guided_conversation.set_artifact_dict(artifact_dict)
        else:
            logger.error("artifact_dict unavailable.")

        conversation_status = Status.UNDEFINED
        next_step_name = None
        # run guided conversation step
        try:
            if message is None:
                user_message = None
            else:
                user_message = message.content
            response_message, conversation_status, next_step_name = await guided_conversation.step_conversation(
                last_user_message=user_message,
            )

            # add the completion to the metadata for debugging
            deepmerge.always_merger.merge(
                metadata,
                {
                    "debug": {
                        f"{method_metadata_key}": {"response": response_message},
                    }
                },
            )

        except Exception as e:
            logger.exception(f"exception occurred processing guided conversation: {e}")
            response_message = "An error occurred while processing the guided conversation."
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
                content=response_message,
                message_type=MessageType.chat,
                metadata=metadata,
            )
        )

        # Need to add a good way to stop mode if an exception occurs.
        # Also need to update the gc state turn count to 0 (and any thing else that needs to be reset) once conversation is over... or exception occurs?)

        return conversation_status, next_step_name

    async def _draft_outline(
        self,
        config: AssistantConfigModel,
        context: ConversationContext,
        message: ConversationMessage | None,
        metadata: dict[str, Any] = {},
    ) -> tuple[Status, StepName | None]:
        method_metadata_key = "draft_outline"

        # get conversation related info -- for now, if no message, assuming no prior conversation
        conversation = None
        participants_list = None
        if message is not None:
            conversation = await context.get_messages(before=message.id)
            if message.message_type == MessageType.chat:
                conversation.messages.append(message)
            participants_list = await context.get_participants(include_inactive=True)

        # get attachments related info
        attachment_messages = await self._attachments_extension.get_completion_messages_for_attachments(
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

        return Status.USER_COMPLETED, None

    async def _gc_outline_feedback(
        self,
        config: AssistantConfigModel,
        context: ConversationContext,
        message: ConversationMessage | None,
        metadata: dict[str, Any] = {},
    ) -> tuple[Status, StepName | None]:
        method_metadata_key = "document_agent_gc_outline_feedback"

        # Pre-requisites
        if self._state is None:
            logger.error("Document Agent state is None. Returning.")
            return Status.UNDEFINED, StepName.UNDEFINED

        # Run
        gc_outline_feedback_config: GuidedConversationConfigModel = GCDraftOutlineFeedbackConfigModel()

        guided_conversation = GuidedConversation(
            config=config,
            openai_client=openai_client.create_client(config.service_config),
            agent_config=gc_outline_feedback_config,
            conversation_context=context,
        )

        # update artifact
        # This step info approach is not cool. Rewriting code. Need to refactor.
        step_name = self._state.mode.get_step().get_name()
        step_list = self._state.mode.get_step_order()
        step_run_count = None
        for step in step_list:
            list_step_name = step.get("step_name")
            if isinstance(list_step_name, StepName):
                if list_step_name is step_name:
                    # This is bad... "run_count" and "step_name" dependent on implementation in a different function.  Need to cleanup.
                    step_run_count = step.get("run_count")
                    break
                else:
                    # End of list
                    if step is step_list[-1]:
                        logger.error("Document Agent - step %s not found in step order.", step_name)
                        self._state.mode.reset()
                        self._write_state(context)
                        return self._state.mode.get_status(), StepName.UNDEFINED  # problem
            else:
                logger.error("Document Agent - step_name of wrong type")
                self._state.mode.reset()
                self._write_state(context)
                return self._state.mode.get_status(), StepName.UNDEFINED  # problem

        if not isinstance(step_run_count, int):
            logger.error("Document Agent - step %s in step order does run_count not of type int.", step_name)
            self._state.mode.reset()
            self._write_state(context)
            return self._state.mode.get_status(), StepName.UNDEFINED  # problem
        else:
            match step_run_count:
                case 0:
                    conversation_status_str = "user_initiated"
                case _:
                    conversation_status_str = "user_returned"

        filenames = await self._attachments_extension.get_attachment_filenames(context)
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

        conversation_status = Status.UNDEFINED
        next_step_name = None
        # run guided conversation step
        try:
            if message is None:
                user_message = None
            else:
                user_message = message.content
            response_message, conversation_status, next_step_name = await guided_conversation.step_conversation(
                last_user_message=user_message,
            )

            # add the completion to the metadata for debugging
            deepmerge.always_merger.merge(
                metadata,
                {
                    "debug": {
                        f"{method_metadata_key}": {"response": response_message},
                    }
                },
            )

        except Exception as e:
            logger.exception(f"exception occurred processing guided conversation: {e}")
            response_message = "An error occurred while processing the guided conversation."
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
                content=response_message,
                message_type=MessageType.chat,
                metadata=metadata,
            )
        )

        # Need to add a good way to stop mode if an exception occurs.
        # Also need to update the gc state turn count to 0 (and any thing else that needs to be reset) once conversation is over... or exception occurs?)

        return conversation_status, next_step_name

    async def _draft_content(
        self,
        config: AssistantConfigModel,
        context: ConversationContext,
        message: ConversationMessage | None,
        metadata: dict[str, Any] = {},
    ) -> tuple[Status, StepName | None]:
        method_metadata_key = "draft_content"

        # get conversation related info -- for now, if no message, assuming no prior conversation
        conversation = None
        participants_list = None
        if message is not None:
            conversation = await context.get_messages(before=message.id)
            if message.message_type == MessageType.chat:
                conversation.messages.append(message)
            participants_list = await context.get_participants(include_inactive=True)

        # get attachments related info
        attachment_messages = await self._attachments_extension.get_completion_messages_for_attachments(
            context, config=config.agents_config.attachment_agent
        )

        # create chat completion messages
        chat_completion_messages: list[ChatCompletionMessageParam] = []
        chat_completion_messages.append(_draft_content_main_system_message())
        if conversation is not None and participants_list is not None:
            chat_completion_messages.append(
                _chat_history_system_message(conversation.messages, participants_list.participants)
            )
        chat_completion_messages.extend(attachment_messages)

        # get outline related info
        if path.exists(storage_directory_for_context(context) / "document_agent/outline.txt"):
            document_outline = (storage_directory_for_context(context) / "document_agent/outline.txt").read_text()
            if document_outline is not None:
                chat_completion_messages.append(_outline_system_message(document_outline))

        if path.exists(storage_directory_for_context(context) / "document_agent/content.txt"):
            document_content = (storage_directory_for_context(context) / "document_agent/content.txt").read_text()
            if document_content is not None:  # only grabs previously written content, not all yet.
                chat_completion_messages.append(_content_system_message(document_content))

        # make completion call to openai
        content: str | None = None
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

        if content is not None:
            # store only latest version for now (will keep all versions later as need arises)
            (storage_directory_for_context(context) / "document_agent/content.txt").write_text(message_content)

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

        return Status.USER_COMPLETED, None

    # endregion


#
# region Helpers
#


def _draft_outline_main_system_message() -> ChatCompletionSystemMessageParam:
    message: ChatCompletionSystemMessageParam = {"role": "system", "content": draft_outline_main_system_message}
    return message


def _draft_content_main_system_message() -> ChatCompletionSystemMessageParam:
    message: ChatCompletionSystemMessageParam = {
        "role": "system",
        "content": draft_content_continue_main_system_message,
    }
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
    message: ChatCompletionSystemMessageParam = {
        "role": "system",
        "content": (f"<EXISTING_OUTLINE>{outline}</EXISTING_OUTLINE>"),
    }
    return message


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
