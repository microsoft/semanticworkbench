import logging
from typing import Any

from assistant_extensions.attachments import AttachmentsExtension
from semantic_workbench_api_model.workbench_model import (
    ConversationMessage,
)
from semantic_workbench_assistant.assistant_app import ConversationContext

from ..config import AssistantConfigModel
from .document.guided_conversation import GC_UserDecision
from .document.state import (
    ModeName,
    ModeStatus,
    State,
    StepDraftContent,
    StepDraftOutline,
    StepFinish,
    StepGetContentFeedback,
    StepGetOutlineFeedback,
    StepName,
    StepStatus,
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

    async def create_document(
        self,
        config: AssistantConfigModel,
        context: ConversationContext,
        message: ConversationMessage | None,
        metadata: dict[str, Any] = {},
    ) -> bool:
        return await self._run(ModeName.DRAFT_PAPER, config, context, message, metadata)

    async def create_outline(
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
        state = read_document_agent_conversation_state(context)
        logger.info("Document Agent: State loaded.")

        try:
            # Execute
            logger.info("Document Agent: Mode executing. ModeName: %s", mode_name)
            state.mode_status = await self._mode_execute(state, config, context, message, metadata)
            logger.info(
                "Document Agent: Mode executed. ModeName: %s, Resulting ModeStatus: %s, Resulting StepName: %s, Resulting StepStatus: %s",
                mode_name,
                state.mode_status,
                state.current_step_name,
                state.current_step_status,
            )
        except Exception:
            logger.exception("Document Agent: Mode execution failed.")
            return False

        else:
            # Write state after successful execution
            write_document_agent_conversation_state(context, state)

        return True

    async def _mode_execute(
        self,
        state: State,
        config: AssistantConfigModel,
        context: ConversationContext,
        message: ConversationMessage | None,
        metadata: dict[str, Any] = {},
    ) -> ModeStatus:
        loop_count = 0
        while state.current_step_status is StepStatus.NOT_COMPLETED:
            loop_count += 1
            # Execute step method
            logger.info(
                "Document Agent: Step executing. Current StepName: %s, Current StepStatus: %s",
                state.current_step_name,
                state.current_step_status,
            )

            match state.current_step_name:
                case StepName.DRAFT_OUTLINE:
                    step = StepDraftOutline()

                case StepName.GC_GET_OUTLINE_FEEDBACK:
                    step = StepGetOutlineFeedback()

                case StepName.DRAFT_CONTENT:
                    step = StepDraftContent()

                case StepName.GC_GET_CONTENT_FEEDBACK:
                    step = StepGetContentFeedback()

                case StepName.FINISH:
                    step = StepFinish()

            (
                new_step_status,
                new_gc_user_decision,
            ) = await step.execute(
                run_count=state.step_run_count.get(state.current_step_name) or 0,
                attachments_ext=self._attachments_extension,
                config=config,
                context=context,
                message=message if loop_count == 1 else None,
                metadata=metadata,
            )
            logger.info(
                "Document Agent: Step executed. Current StepName: %s, Resulting StepStatus: %s",
                state.current_step_name,
                new_step_status,
            )
            state.step_run_count[state.current_step_name] = state.step_run_count.get(state.current_step_name, 0) + 1
            state.current_step_status = new_step_status

            # Workflow StepStatus check
            match new_step_status:
                case StepStatus.NOT_COMPLETED:
                    state.mode_status = ModeStatus.NOT_COMPLETED
                    logger.info(
                        "Document Agent: Getting more user input. Remaining in step. StepName: %s",
                        state.current_step_name,
                    )
                    break  # ok - get more user input

                case StepStatus.USER_COMPLETED:
                    state.mode_status = ModeStatus.USER_COMPLETED

                    def get_next_step(current_step_name: StepName, user_decision: GC_UserDecision) -> StepName:
                        logger.info("Document Agent State: Getting next step.")

                        match current_step_name:
                            case StepName.DRAFT_OUTLINE:
                                return StepName.GC_GET_OUTLINE_FEEDBACK
                            case StepName.GC_GET_OUTLINE_FEEDBACK:
                                match user_decision:
                                    case GC_UserDecision.UPDATE_OUTLINE:
                                        return StepName.DRAFT_OUTLINE
                                    case GC_UserDecision.DRAFT_PAPER:
                                        return StepName.DRAFT_CONTENT
                                    case GC_UserDecision.EXIT_EARLY:
                                        return StepName.FINISH
                                    case _:
                                        raise ValueError("Invalid user decision.")
                            case StepName.DRAFT_CONTENT:
                                return StepName.GC_GET_CONTENT_FEEDBACK
                            case StepName.GC_GET_CONTENT_FEEDBACK:
                                match user_decision:
                                    case GC_UserDecision.UPDATE_CONTENT:
                                        return StepName.DRAFT_CONTENT
                                    case GC_UserDecision.DRAFT_NEXT_CONTENT:
                                        return StepName.DRAFT_CONTENT
                                    case GC_UserDecision.EXIT_EARLY:
                                        return StepName.FINISH
                                    case _:
                                        raise ValueError("Invalid user decision.")
                            case StepName.FINISH:
                                return StepName.FINISH

                    next_step = get_next_step(state.current_step_name, new_gc_user_decision)
                    state.current_step_name = next_step
                    state.current_step_status = StepStatus.NOT_COMPLETED
                    logger.info(
                        "Document Agent: Moving on to next step. Next StepName: %s, Next StepStatus: %s",
                        state.current_step_name,
                        state.current_step_status,
                    )
                    continue  # ok - don't need user input yet

                case StepStatus.USER_EXIT_EARLY:
                    state.mode_status = ModeStatus.USER_EXIT_EARLY
                    logger.info("Document Agent: User exited early. Completed.")
                    break  # ok - done early :)

        return state.mode_status

    # endregion
