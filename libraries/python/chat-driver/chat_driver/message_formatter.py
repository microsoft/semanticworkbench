from typing import Any, Callable

from liquid import Template
from openai.types.chat import ChatCompletionMessageParam

MessageFormatter = Callable[[str, dict[str, Any]], str]


def format_message(message: str, vars: dict[str, Any]) -> str:
    """
    Format a message with the given variables using the Python format method.
    """
    if message and vars:
        for key, value in vars.items():
            try:
                message = message.format(**{key: value})
            except KeyError:
                pass
    return message


def liquid_format(message: str, vars: dict[str, Any]) -> str:
    """
    Format a message with the given variables using the Liquid template engine.
    """
    out = message
    if not message:
        return message
    template = Template(message)
    out = template.render(**vars)
    return out


def system_message(
    content: str, var: dict[str, Any] | None = None, formatter: MessageFormatter = format_message
) -> ChatCompletionMessageParam:
    if var:
        content = formatter(content, var)
    return {"role": "system", "content": content}


def user_message(
    content: str, var: dict[str, Any] | None = None, formatter: MessageFormatter = format_message
) -> ChatCompletionMessageParam:
    if var:
        content = formatter(content, var)
    return {"role": "user", "content": content}


def assistant_message(
    content: str, var: dict[str, Any] | None = None, formatter: MessageFormatter = format_message
) -> ChatCompletionMessageParam:
    if var:
        content = formatter(content, var)
    return {"role": "assistant", "content": content}
