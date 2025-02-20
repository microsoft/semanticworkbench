from typing import Any, Callable, Iterable, Literal, Optional

from assistant_extensions.ai_clients.model import (
    CompletionMessage,
    CompletionMessageImageContent,
    CompletionMessageTextContent,
)
from liquid import Template
from openai.types.chat import (
    ChatCompletionAssistantMessageParam,
    ChatCompletionDeveloperMessageParam,
    ChatCompletionMessageParam,
    ChatCompletionMessageToolCallParam,
    ChatCompletionSystemMessageParam,
    ChatCompletionUserMessageParam,
)


def truncate_messages_for_logging(
    messages: list[ChatCompletionMessageParam],
    truncate_messages_for_roles: set[Literal["user", "system", "developer", "assistant", "tool", "function"]] = {
        "user",
        "system",
        "developer",
        "assistant",
    },
    maximum_content_length: int = 500,
    filler_text: str = " ...truncated... ",
) -> list[dict]:
    """
    Truncates message contents for logging purposes.
    """
    results = []
    for message in messages:
        if message["role"] not in truncate_messages_for_roles:
            results.append(message)
            continue

        content = message.get("content")
        if not content:
            results.append(message)
            continue

        match content:
            case str():
                compressed = truncate_string(content, maximum_content_length, filler_text)
                message["content"] = compressed
                results.append(message)

            case list():
                compressed = apply_truncation_to_list(content, maximum_content_length, filler_text)
                message["content"] = compressed  # type: ignore
                results.append(message)

    return results


def truncate_string(string: str, maximum_length: int, filler_text: str) -> str:
    if len(string) <= maximum_length:
        return string

    head_tail_length = (maximum_length - len(filler_text)) // 2

    return string[:head_tail_length] + filler_text + string[-head_tail_length:]


def apply_truncation_to_list(list_: list, maximum_length: int, filler_text: str) -> list:
    for part in list_:
        for key, value in part.items():
            match value:
                case str():
                    part[key] = truncate_string(value, maximum_length, filler_text)

                case dict():
                    part[key] = apply_truncation_to_dict(value, maximum_length, filler_text)
    return list_


def apply_truncation_to_dict(dict_: dict, maximum_length: int, filler_text: str) -> dict:
    for key, value in dict_.items():
        match value:
            case str():
                dict_[key] = truncate_string(value, maximum_length, filler_text)

            case dict():
                dict_[key] = apply_truncation_to_dict(value, maximum_length, filler_text)
    return dict_


MessageFormatter = Callable[[str, dict[str, Any]], str]


def format_with_dict(template: str, vars: dict[str, Any]) -> str:
    """
    Format a string with the given variables using the Python format method.
    """
    parsed = template
    for key, value in vars.items():
        try:
            parsed = template.format(**{key: value})
        except KeyError:
            pass
    return parsed


def format_with_liquid(template: str, vars: dict[str, Any]) -> str:
    """
    Format a string with the given variables using the Liquid template engine.
    """
    parsed = template
    if not vars:
        return template
    liquid_template = Template(template)
    parsed = liquid_template.render(**vars)
    return parsed


def create_system_message(
    content: str, var: dict[str, Any] | None = None, formatter: MessageFormatter = format_with_liquid
) -> ChatCompletionSystemMessageParam:
    if var:
        content = formatter(content, var)
    return {"role": "system", "content": content}


def create_developer_message(
    content: str, var: dict[str, Any] | None = None, formatter: MessageFormatter = format_with_liquid
) -> ChatCompletionDeveloperMessageParam:
    if var:
        content = formatter(content, var)
    return {"role": "developer", "content": content}


def create_user_message(
    content: str | list[CompletionMessageImageContent | CompletionMessageTextContent],
    var: dict[str, Any] | None = None,
    formatter: MessageFormatter = format_with_liquid,
) -> ChatCompletionUserMessageParam:
    if isinstance(content, list):
        items = []
        for item in content:
            if item.type == "text":
                if var:
                    item.text = formatter(item.text, var)
                items.append({"type": "text", "text": item.text})
            elif item.type == "image":
                items.append({"type": "image_url", "image_url": {"url": item.data}})
        return {"role": "user", "content": items}
    if var:
        content = formatter(content, var)
    return {"role": "user", "content": content}


def create_assistant_message(
    content: str,
    refusal: Optional[str] = None,
    tool_calls: Iterable[ChatCompletionMessageToolCallParam] | None = None,
    var: dict[str, Any] | None = None,
    formatter: MessageFormatter = format_with_liquid,
) -> ChatCompletionAssistantMessageParam:
    if var:
        content = formatter(content, var)
    message = ChatCompletionAssistantMessageParam(role="assistant", content=content, refusal=refusal)
    if tool_calls is not None:
        message["tool_calls"] = tool_calls
    return message


def convert_from_completion_messages(
    completion_message: Iterable[CompletionMessage],
) -> list[ChatCompletionMessageParam]:
    """
    Convert a list of service-agnostic completion message to a list of OpenAI chat completion message parameter.
    """
    messages: list[ChatCompletionMessageParam] = []

    for message in completion_message:
        if message.role == "system" and isinstance(message.content, str):
            messages.append(
                create_system_message(
                    content=message.content,
                )
            )
            continue

        if message.role == "developer" and isinstance(message.content, str):
            messages.append(
                create_developer_message(
                    content=message.content,
                )
            )
            continue

        if message.role == "assistant" and isinstance(message.content, str):
            messages.append(
                create_assistant_message(
                    content=message.content,
                )
            )
            continue

        messages.append(
            create_user_message(
                content=message.content,
            )
        )

    return messages
