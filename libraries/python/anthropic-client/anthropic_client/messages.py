from typing import Any, Callable, Iterable, Literal, Union

from anthropic.types import ImageBlockParam, MessageParam, TextBlockParam
from anthropic.types.beta import BetaImageBlockParam, BetaMessageParam, BetaTextBlockParam
from liquid import Template
from llm_client.model import (
    CompletionMessage,
    CompletionMessageImageContent,
    CompletionMessageTextContent,
)


def truncate_messages_for_logging(
    messages: list[MessageParam],
    truncate_messages_for_roles: set[Literal["user", "system", "assistant", "tool", "function"]] = {
        "user",
        "system",
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


def create_system_prompt(
    content: str, var: dict[str, Any] | None = None, formatter: MessageFormatter = format_with_liquid
) -> str:
    if var:
        content = formatter(content, var)
    return content.strip()


def create_user_message(
    content: str | list[CompletionMessageImageContent | CompletionMessageTextContent],
    var: dict[str, Any] | None = None,
    formatter: MessageFormatter = format_with_liquid,
) -> MessageParam:
    if isinstance(content, list):
        items: Iterable[Union[TextBlockParam, ImageBlockParam]] = []
        for item in content:
            if item.type == "text":
                if var:
                    item.text = formatter(item.text, var)
                items.append(TextBlockParam(type="text", text=item.text.strip()))
            elif item.type == "image":
                items.append(
                    ImageBlockParam(
                        type="image",
                        source={
                            "type": "base64",
                            "data": item.data,
                            "media_type": item.media_type,
                        },
                    )
                )
        return MessageParam(role="user", content=items)

    if var:
        content = formatter(content, var)
    return MessageParam(role="user", content=content.strip())


def create_assistant_message(
    content: str,
    var: dict[str, Any] | None = None,
    formatter: MessageFormatter = format_with_liquid,
) -> MessageParam:
    if var:
        content = formatter(content, var)
    return MessageParam(role="assistant", content=content.strip())


def create_user_beta_message(
    content: str | list[CompletionMessageImageContent | CompletionMessageTextContent],
    var: dict[str, Any] | None = None,
    formatter: MessageFormatter = format_with_liquid,
) -> BetaMessageParam:
    if isinstance(content, list):
        items: Iterable[Union[BetaTextBlockParam, BetaImageBlockParam]] = []
        for item in content:
            if item.type == "text":
                if var:
                    item.text = formatter(item.text, var)
                items.append(BetaTextBlockParam(type="text", text=item.text.strip()))
            elif item.type == "image":
                items.append(
                    BetaImageBlockParam(
                        type="image",
                        source={
                            "type": "base64",
                            "data": item.data,
                            "media_type": item.media_type,
                        },
                    )
                )
        return BetaMessageParam(role="user", content=items)

    if var:
        content = formatter(content, var)
    return BetaMessageParam(role="user", content=content.strip())


def create_assistant_beta_message(
    content: str,
    var: dict[str, Any] | None = None,
    formatter: MessageFormatter = format_with_liquid,
) -> BetaMessageParam:
    if var:
        content = formatter(content, var)
    return BetaMessageParam(role="assistant", content=content.strip())


def convert_from_completion_messages(
    completion_messages: Iterable[CompletionMessage],
) -> list[MessageParam]:
    """
    Convert a service-agnostic completion message to an Anthropic message parameter.
    """
    messages: list[MessageParam] = []

    for message in completion_messages:
        # Anthropic API does not support system role in messages, so convert system role to user role
        if (message.role == "system" or message.role == "assistant") and isinstance(message.content, str):
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


def beta_convert_from_completion_messages(
    completion_messages: Iterable[CompletionMessage],
) -> list[BetaMessageParam]:
    """
    Convert a service-agnostic completion message to an Anthropic message parameter.
    """
    messages: list[BetaMessageParam] = []

    for message in completion_messages:
        # Anthropic API does not support system role in messages, so convert system role to user role
        if (message.role == "system" or message.role == "assistant") and isinstance(message.content, str):
            messages.append(
                create_assistant_beta_message(
                    content=message.content,
                )
            )
            continue

        messages.append(
            create_user_beta_message(
                content=message.content,
            )
        )
    return messages
