# Copyright (c) Microsoft. All rights reserved.

from mcp_extensions.llm.llm_types import MessageT


def format_chat_history(chat_history: list[MessageT]) -> str:
    formatted_chat_history = ""
    for message in chat_history:
        formatted_chat_history += f"[{message.role.value}]: {message.content}\n"
    return formatted_chat_history.strip()
