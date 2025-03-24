# Copyright (c) Microsoft. All rights reserved.

from copy import deepcopy
from typing import Any

from liquid import render
from pydantic import BaseModel

from mcp_extensions.llm.llm_types import MessageT


def _apply_templates(value: Any, variables: dict[str, str]) -> Any:
    """Recursively applies Liquid templating to all string fields within the given value."""
    if isinstance(value, str):
        return render(value, **variables)
    elif isinstance(value, list):
        return [_apply_templates(item, variables) for item in value]
    elif isinstance(value, dict):
        return {key: _apply_templates(val, variables) for key, val in value.items()}
    elif isinstance(value, BaseModel):
        # Process each field in the BaseModel by converting it to a dict,
        # applying templating to its values, and then re-instantiating the model.
        processed_data = {key: _apply_templates(val, variables) for key, val in value.model_dump().items()}
        return value.__class__(**processed_data)
    else:
        return value


def compile_messages(messages: list[MessageT], variables: dict[str, str]) -> list[MessageT]:
    """Compiles messages using Liquid templating and the provided variables.
    Calls render(content_part, **variables) on each text content part.

    Args:
        messages: List of MessageT where content can contain Liquid templates.
        variables: The variables to inject into the templates.

    Returns:
        The same list of messages with the content parts injected with the variables.
    """
    messages_formatted = deepcopy(messages)
    messages_formatted = [_apply_templates(message, variables) for message in messages_formatted]
    return messages_formatted


def format_chat_history(chat_history: list[MessageT]) -> str:
    formatted_chat_history = ""
    for message in chat_history:
        formatted_chat_history += f"[{message.role.value}]: {message.content}\n"
    return formatted_chat_history.strip()
