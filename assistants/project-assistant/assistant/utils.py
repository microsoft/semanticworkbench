"""
Utility functions for the project assistant module.

This module provides common utility functions used across the project assistant
codebase, helping to reduce code duplication and maintain consistency.
"""

import pathlib
from typing import Optional, Tuple

from semantic_workbench_assistant.assistant_app import ConversationContext

from .logging import logger

CONTEXT_TRANSFER_TEMPLATE_ID = "knowledge_transfer"


def is_context_transfer_assistant(context: ConversationContext) -> bool:
    """
    Determine if the assistant is using the context transfer template.

    Args:
        context: The conversation context containing assistant information

    Returns:
        True if this is a context transfer assistant, False otherwise
    """
    return context.assistant._template_id == CONTEXT_TRANSFER_TEMPLATE_ID


def load_text_include(filename) -> str:
    """
    Helper for loading an include from a text file.

    Args:
        filename: The name of the text file to load from the text_includes directory

    Returns:
        The content of the text file
    """
    # Get directory relative to this module
    directory = pathlib.Path(__file__).parent

    # Get the file path for the prompt file
    file_path = directory / "text_includes" / filename

    # Read the prompt from the file
    return file_path.read_text()


async def get_current_user(context: ConversationContext) -> Tuple[Optional[str], Optional[str]]:
    """
    Extract the current user ID and name from the conversation context.

    Args:
        context: The conversation context to extract user information from

    Returns:
        A tuple containing (user_id, user_name), both may be None if no user is found
    """
    participants = await context.get_participants()
    user_id = None
    user_name = None

    for participant in participants.participants:
        if participant.role == "user":
            user_id = participant.id
            user_name = participant.name
            break

    return user_id, user_name


async def get_current_user_id(context: ConversationContext) -> Optional[str]:
    """
    Extract just the current user ID from the conversation context.

    Args:
        context: The conversation context to extract user information from

    Returns:
        The user ID, or None if no user is found
    """
    user_id, _ = await get_current_user(context)
    return user_id


async def require_current_user(context: ConversationContext, operation_name: str) -> Optional[str]:
    """
    Extract the current user ID and log an error if none is found.

    Args:
        context: The conversation context to extract user information from
        operation_name: Name of the operation requiring a user, for error logging

    Returns:
        The user ID, or None if no user is found (after logging an error)
    """
    user_id = await get_current_user_id(context)

    if not user_id:
        logger.error(f"Cannot {operation_name}: no user found in conversation")

    return user_id
