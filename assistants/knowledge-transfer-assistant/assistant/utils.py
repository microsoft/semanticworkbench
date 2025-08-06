"""
Utility functions for the knowledge transfer assistant module.

This module provides common utility functions used across the knowledge transfer assistant
codebase, helping to reduce code duplication and maintain consistency.
"""

import pathlib

from semantic_workbench_assistant.assistant_app import ConversationContext

from assistant.errors import NoUserException
from assistant.string_utils import render

DEFAULT_TEMPLATE_ID = "default"


def load_text_include(filename: str, replacements: dict[str, str] = {}) -> str:
    """
    Helper for loading an include from a text file.

    Args:
        filename: The name of the text file to load from the text_includes directory

    Returns:
        The content of the text file
    """
    directory = pathlib.Path(__file__).parent
    file_path = directory / "text_includes" / filename
    text = file_path.read_text()
    return render(text, replacements)


async def get_current_user(
    context: ConversationContext,
) -> tuple[str, str | None]:
    participants = await context.get_participants()
    user_id = None
    user_name = None

    for participant in participants.participants:
        if participant.role == "user":
            user_id = participant.id
            user_name = participant.name
            break

    if not user_id:
        raise NoUserException

    return user_id, user_name


async def get_current_user_id(context: ConversationContext) -> str:
    user_id, _ = await get_current_user(context)
    return user_id
