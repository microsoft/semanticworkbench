class AssistantError(Exception):
    pass


class BadRequestError(AssistantError):
    pass


class ConflictError(BadRequestError):
    pass


class NotFoundError(BadRequestError):
    pass
