import json
from typing import Any

from openai.types.chat import (
    ChatCompletionAssistantMessageParam,
    ParsedChatCompletion,
    ParsedChatCompletionMessage,
)
from openai.types.chat.completion_create_params import (
    ResponseFormat,
)
from pydantic import BaseModel

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
