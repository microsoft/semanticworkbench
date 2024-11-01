from enum import StrEnum


class Status(StrEnum):
    UNDEFINED = "undefined"
    NOT_COMPLETED = "not_completed"
    UPDATE_OUTLINE = "update_outline"
    USER_COMPLETED = "user_completed"
    USER_EXIT_EARLY = "user_exit_early"
