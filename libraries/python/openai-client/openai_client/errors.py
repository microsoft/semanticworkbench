from typing import Any

from openai import (
    APIConnectionError,
    APIStatusError,
    BadRequestError,
    RateLimitError,
)
from openai.types.chat import (
    ParsedChatCompletion,
)


class CompletionInvalidError(Exception):
    def __init__(self, message: str, body: dict[str, Any] | None = None) -> None:
        self.message = message
        self.body = body
        super().__init__(self.message)


class CompletionIsNoneError(CompletionInvalidError):
    def __init__(self) -> None:
        super().__init__("The completion response is None.")


class CompletionRefusedError(CompletionInvalidError):
    def __init__(self, refusal: str) -> None:
        super().__init__(f"The model refused to complete the response: {refusal}", {"refusal": refusal})


class CompletionWithoutStopError(CompletionInvalidError):
    def __init__(self, finish_reason: str) -> None:
        super().__init__(f"The model did not complete the response: {finish_reason}", {"finish_reason": finish_reason})


class CompletionError(Exception):
    def __init__(self, error: Exception) -> None:
        if isinstance(error, APIConnectionError):
            message = f"The server could not be reached: {error.__cause__}"
            body = error.body
        elif isinstance(error, RateLimitError):
            message = "A 429 status code was received (rate limited); we should back off a bit."
            body = error.body
        elif isinstance(error, BadRequestError):
            message = f"A 400 status code was received. {error.message}"
            body = error.body
        elif isinstance(error, APIStatusError):
            message = f"Another non-200-range status code was received. {error.status_code}: {error.message}"
            body = error.body
        elif isinstance(error, CompletionInvalidError):
            message = error.message
            body = error.body
        else:
            message = f"An unknown error occurred ({error.__class__.__name__})."
            body = str(error)

        self.message = message
        self.body = body
        super().__init__(message)


def validate_completion(completion: ParsedChatCompletion | None) -> None:
    if completion is None:
        raise CompletionIsNoneError()

    # Check for refusal.
    refusal = completion.choices[0].message.refusal
    if refusal:
        raise CompletionRefusedError(refusal)

    # Check "finish_reason" for "max_tokens" or "stop" to see if the response is incomplete.
    finish_reason = completion.choices[0].finish_reason
    if finish_reason not in ["stop", "tool_calls", None]:
        raise CompletionWithoutStopError(finish_reason)
