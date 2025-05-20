"""
Utility functions for the project assistant module.

This module provides common utility functions used across the project assistant
codebase, helping to reduce code duplication and maintain consistency.
"""

import pathlib
from enum import Enum
from typing import Optional, Tuple

from semantic_workbench_assistant.assistant_app import ConversationContext

from .logging import logger

KNOWLEDGE_TRANSFER_TEMPLATE_ID = "knowledge_transfer"
DEFAULT_TEMPLATE_ID = "default"


class ConfigurationTemplate(Enum):
    """
    This assistant can be in one of two different template configurations. It
    behaves quite differently based on which configuration it it in.
    """

    PROJECT_ASSISTANT = DEFAULT_TEMPLATE_ID
    KNOWLEDGE_TRANSFER_ASSISTANT = KNOWLEDGE_TRANSFER_TEMPLATE_ID


def get_template(context: ConversationContext) -> ConfigurationTemplate:
    template_id = context.assistant._template_id or DEFAULT_TEMPLATE_ID
    return (
        ConfigurationTemplate.PROJECT_ASSISTANT
        if template_id == DEFAULT_TEMPLATE_ID
        else ConfigurationTemplate.KNOWLEDGE_TRANSFER_ASSISTANT
    )


def is_knowledge_transfer_assistant(context: ConversationContext) -> bool:
    """
    Determine if the assistant is using the context transfer template.
    """
    return context.assistant._template_id == KNOWLEDGE_TRANSFER_TEMPLATE_ID


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
