"""
Utility functions for handling attachments in chat messages.
"""

from typing import Awaitable, Callable, Sequence

from openai.types.chat import ChatCompletionMessageParam
from semantic_workbench_assistant.assistant_app.context import ConversationContext

from .. import state


async def message_with_recent_attachments(
    context: ConversationContext,
    latest_user_message: str | None,
    get_attachment_messages: Callable[[Sequence[str]], Awaitable[Sequence[ChatCompletionMessageParam]]],
) -> str:
    files = await context.get_files()

    new_filenames = set()

    async with state.agent_state(context) as agent_state:
        max_timestamp = agent_state.most_recent_attachment_timestamp
        for file in files.files:
            if file.updated_datetime.timestamp() <= agent_state.most_recent_attachment_timestamp:
                continue

            max_timestamp = max(file.updated_datetime.timestamp(), max_timestamp)
            new_filenames.add(file.filename)

        agent_state.most_recent_attachment_timestamp = max_timestamp

    attachment_messages = await get_attachment_messages(list(new_filenames))

    return "\n\n".join(
        (
            latest_user_message or "",
            *(
                str(attachment.get("content"))
                for attachment in attachment_messages
                if "<ATTACHMENT>" in str(attachment.get("content", ""))
            ),
        ),
    )


async def attachment_for_filename(
    filename: str, get_attachment_messages: Callable[[Sequence[str]], Awaitable[Sequence[ChatCompletionMessageParam]]]
) -> str:
    attachment_messages = await get_attachment_messages([filename])
    return "\n\n".join(
        (
            str(attachment.get("content"))
            for attachment in attachment_messages
            if "<ATTACHMENT>" in str(attachment.get("content", ""))
        )
    )
