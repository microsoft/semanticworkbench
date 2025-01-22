# FIXME: move these to openai-client lib

from typing import Iterable

from assistant_extensions.ai_clients.model import (
    CompletionMessage,
)
from openai.types.chat import (
    ChatCompletionMessageParam,
    ChatCompletionToolMessageParam,
)


from openai_client import create_system_message, create_user_message, create_assistant_message

def create_tool_message(
    content: str,
    tool_call_id: str,
) -> ChatCompletionToolMessageParam:
    return {"role": "tool", "content": content, "tool_call_id": tool_call_id}

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

        if message.role == "assistant" and isinstance(message.content, str):
            messages.append(
                create_assistant_message(
                    content=message.content,
                )
            )
            continue

        if message.role == "tool" and message.tool_call_id is not None and isinstance(message.content, str):
            messages.append(
                create_tool_message(
                    tool_call_id=message.tool_call_id,
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
