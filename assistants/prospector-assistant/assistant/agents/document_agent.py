import logging
from typing import Any

from assistant_extensions.attachments import AttachmentsExtension
from semantic_workbench_api_model.workbench_model import (
    ConversationMessage,
)
from semantic_workbench_assistant.assistant_app import ConversationContext

from ..config import AssistantConfigModel
from .document.state import (
    Mode,
    ModeName,
    ModeStatus,
    State,
    StepName,
    StepStatus,
    mode_prerequisite_check,
    read_document_agent_conversation_state,
    write_document_agent_conversation_state,
)

logger = logging.getLogger(__name__)


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

    def _write_state(self, state: State, context: ConversationContext) -> None:
        if state is None:
            logger.error("Document Agent: local state is None. Cannot write to storage.")
            return
        write_document_agent_conversation_state(context, state.model_dump())

    def _read_state(self, context: ConversationContext) -> State:
        state_dict = read_document_agent_conversation_state(context)
        if state_dict is not None:
            state = State(**state_dict)
        else:
            logger.info("Document Agent: no state found in storage. Returning an undefined state.")
            state = State()
        self._state = state
        return state

    async def create_document(
        self,
        config: AssistantConfigModel,
        context: ConversationContext,
        message: ConversationMessage | None,
        metadata: dict[str, Any] = {},
    ) -> bool:
        return await self._run(ModeName.DRAFT_OUTLINE, config, context, message, metadata)

    #
    # region mode methods
    #
    async def _run(
        self,
        mode_name: ModeName,
        config: AssistantConfigModel,
        context: ConversationContext,
        message: ConversationMessage | None,
        metadata: dict[str, Any] = {},
    ) -> bool:
        # Load State
        logger.info("Document Agent: State loading.")
        state = self._read_state(context)
        if state is None:
            logger.error("Document Agent: State is None. Returning.")
            return False
        if not state.mode.is_running():
            state.set_mode(Mode(name=mode_name, status=ModeStatus.INITIATED))
            self._write_state(state, context)
        logger.info("Document Agent: State loaded.")

        # Prerequisites
        result = mode_prerequisite_check(state, mode_name)
        if result is False:
            logger.error("Document Agent: Mode %s prerequisite check failed. Resetting mode. Returning.", mode_name)
            state.mode.reset()
            self._write_state(state, context)
            return False

        # Execute
        logger.info("Document Agent: Mode executing. ModeName: %s", mode_name)
        mode_result_status = await self._mode_execute(state, config, context, message, metadata)
        logger.info(
            "Document Agent: Mode executed. ModeName: %s, Resulting ModeStatus: %s", mode_name, mode_result_status
        )
        if mode_result_status is ModeStatus.UNDEFINED:
            logger.error(
                "Document Agent: Running mode %s resulted in mode status %s. Resetting mode. Returning",
                mode_name,
                mode_result_status,
            )
            state.mode.reset()
            self._write_state(state, context)
            return False
        else:
            state.mode.set_status(mode_result_status)
            self._write_state(state, context)
            return True

    async def _mode_execute(
        self,
        state: State,
        config: AssistantConfigModel,
        context: ConversationContext,
        message: ConversationMessage | None,
        metadata: dict[str, Any] = {},
    ) -> ModeStatus:
        current_step_name = state.mode.get_step().get_name()
        current_step_status = state.mode.get_step().get_status()

        while current_step_status is StepStatus.INITIATED or current_step_status is StepStatus.NOT_COMPLETED:
            # Execute step method
            logger.info(
                "Document Agent: Step executing. Current StepName: %s, Current StepStatus: %s",
                current_step_name,
                current_step_status,
            )
            execute_step_method = state.mode.get_step().execute
            if execute_step_method is not None:
                step_data = state.get_step_data(current_step_name)
                new_step_status = await execute_step_method(
                    step_data, self._attachments_extension, config, context, message, metadata
                )
                logger.info(
                    "Document Agent: Step executed. Current StepName: %s, Resulting StepStatus: %s",
                    current_step_name,
                    new_step_status,
                )
                state.mode.get_step().set_status(new_step_status)
                self._write_state(state, context)
            else:
                logger.error("Document Agent: step.execute not defined for StepName: %s.", current_step_name)
                break

            # Update step data
            run_count_key = "run_count"
            logger.info(
                "Document Agent: StepData updating (%s). Current StepName: %s", run_count_key, current_step_name
            )
            step_data = state.get_step_data(current_step_name)
            step_data.run_count += 1
            state.set_step_data(step_data)
            self._write_state(state, context)

            # Workflow StepStatus check
            match new_step_status:
                case StepStatus.NOT_COMPLETED:
                    state.mode.get_step().set_status(new_step_status)
                    state.mode.set_status(ModeStatus.NOT_COMPLETED)
                    self._write_state(state, context)
                    logger.info(
                        "Document Agent: Getting more user input. Remaining in step. StepName: %s", current_step_name
                    )
                    break  # ok - get more user input

                case StepStatus.USER_COMPLETED:
                    if state.mode.get_next_step is not None:
                        next_step = state.mode.get_next_step()
                        if next_step.get_name() is not StepName.UNDEFINED:
                            state.mode.set_step(next_step)
                            self._write_state(state, context)
                            current_step_name = state.mode.get_step().get_name()
                            current_step_status = state.mode.get_step().get_status()  # new step is Status.INITIATED
                            logger.info(
                                "Document Agent: Moving on to next step. Next StepName: %s, Next StepStatus: %s",
                                current_step_name,
                                current_step_status,
                            )
                            continue  # ok - don't need user input yet
                        else:
                            state.mode.set_step(next_step)
                            state.mode.set_status(ModeStatus.USER_COMPLETED)
                            self._write_state(state, context)
                            logger.info("Document Agent: No more steps in mode. Completed.")
                            break  # ok - all done :)
                    else:
                        logger.error(
                            "Document Agent: mode.get_next_step not defined for Mode Name: %s.", state.mode.get_name()
                        )
                        break

                case StepStatus.USER_EXIT_EARLY:
                    state.mode.get_step().set_status(new_step_status)
                    state.mode.set_status(ModeStatus.USER_EXIT_EARLY)
                    self._write_state(state, context)
                    logger.info("Document Agent: User exited early. Completed.")
                    break  # ok - done early :)

                case _:  # UNDEFINED, INITIATED
                    logger.error(
                        "Document Agent: step.execute for StepName: %s resulted in StepStatus: %s. Resetting mode %s.",
                        current_step_name,
                        new_step_status,
                        state.mode.get_name(),
                    )
                    state.mode.reset()
                    self._write_state(state, context)
                    break  # problem

        return state.mode.get_status()

    # endregion


# Not currently used
# async def receive_command(
#    self,
#    config: AssistantConfigModel,
#    context: ConversationContext,
#    message: ConversationMessage,
#    metadata: dict[str, Any] = {},
# ) -> None:
#    self._state = self._read_state(context)
#
#    # remove initial "/". This is not intuitive to me.
#    msg_command_name = message.command_name
#    msg_command_name = msg_command_name.replace("/", "")
#
#    # check if available. If not, ignore for now.
#    command_found = False
#    for command in self.commands:
#        if command.__name__ == msg_command_name:
#            logger.info("Found command %s", message.command_name)
#            command_found = True
#            command(config, context, message, metadata)  # does not handle command with args or async commands
#            break
#    if not command_found:
#        logger.warning("Could not find command %s", message.command_name)

# Not currently used
# def _set_mode_draft_paper(
#    self,
#    config: AssistantConfigModel,
#    context: ConversationContext,
#    message: ConversationMessage | None,
#    metadata: dict[str, Any] = {},
# ) -> None:
#    # Pre-requisites
#    if self._state is None:
#        logger.error("Document Agent state is None. Returning.")
#        return
#
#    mode = self._state.mode
#    if mode.is_running():
#        logger.warning("Document Agent already in mode: %s. Cannot change modes.", mode.get_name())
#        return
#
#    # Run
#    self._state.mode = Mode(name=ModeName.DRAFT_PAPER, status=Status.INITIATED)
#    self._write_state(context)

# not used currently
# async def _mode_draft_paper(
#    self,
#    config: AssistantConfigModel,
#    context: ConversationContext,
#    message: ConversationMessage | None,
#    metadata: dict[str, Any] = {},
# ) -> Status:
#    # Pre-requisites
#    if self._state is None:
#        logger.error("Document Agent state is None. Returning.")
#        return Status.UNDEFINED
#
#    mode = self._state.mode
#    mode_name = mode.get_name()
#    mode_status = mode.get_status()
#
#    if mode_name is not ModeName.DRAFT_PAPER or (
#        mode_status is not Status.NOT_COMPLETED and mode_status is not Status.INITIATED
#    ):
#        logger.error(
#            "Document Agent state mode: %s, mode called: %s, state mode completion status: %s. Resetting Mode.",
#            mode_name,
#            ModeName.DRAFT_PAPER,
#            mode_status,
#        )
#        self._state.mode.reset()
#        self._write_state(context)
#        return self._state.mode.get_status()
#
#    # Setup on first run.
#    if mode_status is Status.INITIATED:
#        self._state.mode.set_step_order(
#            [
#                {"step_name": StepName.DO_DRAFT_OUTLINE, "run_count": 0},
#                {"step_name": StepName.DO_GC_GET_OUTLINE_FEEDBACK, "run_count": 0},
#                {"step_name": StepName.DP_DRAFT_CONTENT, "run_count": 0},
#            ],
#        )
#        logger.info("Document Agent mode (%s) at beginning.", mode_name)
#        first_step_name = self._state.mode.get_step_order()[0].get("step_name")
#        if not isinstance(first_step_name, StepName):
#            logger.error("Document Agent: StepName could not be found in Mode's step order.")
#            self._state.mode.reset()
#            return self._state.mode.get_status()
#        self._state.mode.set_step(Step(name=first_step_name, status=Status.INITIATED))
#        self._write_state(context)
#
#    self._step_name_to_method: dict[StepName, Callable] = {
#        StepName.DO_DRAFT_OUTLINE: self._step_draft_outline,
#        StepName.DO_GC_GET_OUTLINE_FEEDBACK: self._step_gc_get_outline_feedback,
#        StepName.DP_DRAFT_CONTENT: self._step_draft_content,
#    }
#
#    # Run
#    return await self._run_mode(config, context, message, metadata)
