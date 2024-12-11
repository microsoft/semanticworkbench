# # Copyright (c) Microsoft. All rights reserved.

# FIXME: Copied code from Semantic Kernel repo, using as-is despite type errors
# type: ignore

from dataclasses import dataclass

from pydantic import ValidationError
from semantic_kernel import Kernel
from semantic_kernel.connectors.ai.function_calling_utils import kernel_function_metadata_to_function_call_format
from semantic_kernel.contents import ChatMessageContent


@dataclass
class PluginOutput:
    """A wrapper for all Guided Conversation Plugins. This class is used to return the output of a generic plugin.

    Args:
        update_successful (bool): Whether the update was successful.
        messages (list[ChatMessageContent]): A list of messages to be used at the user's digression, it
        contains information about the process of calling the plugin.
    """

    update_successful: bool
    messages: list[ChatMessageContent]


def format_kernel_functions_as_tools(kernel: Kernel, functions: list[str]):
    """Format kernel functions as JSON schemas for custom validation."""
    formatted_tools = []
    for _, kernel_plugin_def in kernel.plugins.items():
        for function_name, function_def in kernel_plugin_def.functions.items():
            if function_name in functions:
                func_metadata = function_def.metadata
                formatted_tools.append(kernel_function_metadata_to_function_call_format(func_metadata))
    return formatted_tools


def update_attempts(
    error: Exception, attempt_id: str, previous_attempts: list[tuple[str, str]]
) -> tuple[list[tuple[str, str]], str]:
    """
    Updates the plugin class attribute list of previous attempts with the current attempt and error message
    (including duplicates).

    Args:
        error (Exception): The error object.
        attempt_id (str): The ID of the current attempt.
        previous_attempts (list): The list of previous attempts.

    Returns:
        str: A formatted (optimized for LLM performance) string of previous attempts, with duplicates removed.
    """
    if isinstance(error, ValidationError):
        error_str = "; ".join([e.get("msg") for e in error.errors()])
        # replace "; Input should be 'Unanswered'" with " or input should be 'Unanswered'" for clarity
        error_str = error_str.replace("; Input should be 'Unanswered'", " or input should be 'Unanswered'")
    else:
        error_str = str(error)
    new_failed_attempt = (attempt_id, error_str)
    previous_attempts.append(new_failed_attempt)

    # Format previous attempts to be more friendly for the LLM
    attempts_list = []
    for attempt, error in previous_attempts:
        attempts_list.append(f"Attempt: {attempt}\nError: {error}")
    llm_formatted_attempts = "\n".join(attempts_list)

    return previous_attempts, llm_formatted_attempts
