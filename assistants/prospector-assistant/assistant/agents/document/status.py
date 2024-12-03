from enum import StrEnum


class Status(StrEnum):
    UNDEFINED = "undefined"
    INITIATED = "initiated"
    NOT_COMPLETED = "not_completed"
    USER_COMPLETED = "user_completed"
    USER_EXIT_EARLY = "user_exit_early"


class StepName(StrEnum):
    UNDEFINED = "undefined"
    DO_DRAFT_OUTLINE = "step_draft_outline"
    DO_GC_GET_OUTLINE_FEEDBACK = "step_gc_get_outline_feedback"
    DO_FINISH = "step_finish"
    DP_DRAFT_CONTENT = "step_draft_content"
