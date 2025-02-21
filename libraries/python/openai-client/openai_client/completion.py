import json
import logging
from time import perf_counter
from typing import Any, Generic, Literal, TypeVar

from openai import AsyncOpenAI, NotGiven
from openai.types.chat import (
    ChatCompletionAssistantMessageParam,
    ChatCompletionMessageParam,
    ParsedChatCompletion,
    ParsedChatCompletionMessage,
)
from openai.types.chat.completion_create_params import (
    ResponseFormat,
)
from pydantic import BaseModel

logger = logging.getLogger(__name__)

DEFAULT_MAX_RETRIES = 3

# The response method can return a text response, a JSON object response, or as
# a Pydantic BaseModel. See the `response` method for more details.
TEXT_RESPONSE_FORMAT: ResponseFormat = {"type": "text"}
JSON_OBJECT_RESPONSE_FORMAT: ResponseFormat = {"type": "json_object"}


def assistant_message_from_completion(completion: ParsedChatCompletion[None]) -> ChatCompletionAssistantMessageParam:
    completion_message: ParsedChatCompletionMessage = completion.choices[0].message
    assistant_message = ChatCompletionAssistantMessageParam(role="assistant")
    if completion_message.tool_calls:
        response_dict = completion_message.model_dump()
        assistant_message["tool_calls"] = response_dict["tool_calls"]
    if completion_message.content:
        assistant_message["content"] = completion_message.content
    return assistant_message


def message_from_completion(completion: ParsedChatCompletion) -> ParsedChatCompletionMessage | None:
    return completion.choices[0].message if completion and completion.choices else None


def message_content_from_completion(completion: ParsedChatCompletion | None) -> str:
    if not completion or not completion.choices or not completion.choices[0].message:
        return ""
    return completion.choices[0].message.content or ""


def message_content_dict_from_completion(completion: ParsedChatCompletion) -> dict[str, Any] | None:
    message = message_from_completion(completion)
    if message:
        if message.parsed:
            if isinstance(message.parsed, BaseModel):
                return message.parsed.model_dump()
            elif isinstance(message.parsed, dict):
                return message.parsed
            else:
                try:  # Try to parse the JSON string.
                    return json.loads(message.parsed)
                except json.JSONDecodeError:
                    return None
        try:
            return json.loads(message.content or "")
        except json.JSONDecodeError:
            return None


class NoResponseChoicesError(Exception):
    pass


class NoParsedMessageError(Exception):
    pass


ResponseModelT = TypeVar("ResponseModelT", bound=BaseModel)


class StructuredResponse(BaseModel, Generic[ResponseModelT]):
    response: ResponseModelT
    metadata: dict[str, Any]


async def completion_structured(
    async_client: AsyncOpenAI,
    messages: list[ChatCompletionMessageParam],
    openai_model: str,
    response_model: type[ResponseModelT],
    max_completion_tokens: int,
    reasoning_effort: Literal["low", "medium", "high"] | None,
) -> StructuredResponse[ResponseModelT]:
    start = perf_counter()

    response_raw = await async_client.beta.chat.completions.with_raw_response.parse(
        messages=messages,
        model=openai_model,
        response_format=response_model,
        reasoning_effort=reasoning_effort or NotGiven(),
        max_completion_tokens=max_completion_tokens,
    )

    headers = {key: value for key, value in response_raw.headers.items()}
    response = response_raw.parse()

    if not response.choices:
        raise NoResponseChoicesError()

    if not response.choices[0].message.parsed:
        raise NoParsedMessageError()

    if response.choices[0].finish_reason != "stop":
        logger.warning("Unexpected finish reason, expected stop; reason: %s", response.choices[0].finish_reason)

    metadata = {
        "request": {
            "model": openai_model,
            "messages": messages,
            "max_completion_tokens": max_completion_tokens,
            "response_format": response_model.model_json_schema(),
            "reasoning_effort": reasoning_effort,
        },
        "response": response.model_dump(),
        "response_headers": headers,
        "response_duration": perf_counter() - start,
    }

    return StructuredResponse(response=response.choices[0].message.parsed, metadata=metadata)
