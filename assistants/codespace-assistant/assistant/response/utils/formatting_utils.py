import logging

from semantic_workbench_api_model.workbench_model import (
    ConversationMessage,
    ConversationParticipant,
)

logger = logging.getLogger(__name__)


def format_message(message: ConversationMessage, participants: list[ConversationParticipant]) -> str:
    """
    Format a conversation message for display.
    """
    conversation_participant = next(
        (participant for participant in participants if participant.id == message.sender.participant_id),
        None,
    )
    participant_name = conversation_participant.name if conversation_participant else "unknown"
    message_datetime = message.timestamp.strftime("%Y-%m-%d %H:%M:%S")
    return f"[{participant_name} - {message_datetime}]: {message.content}"


def get_response_duration_message(response_duration: float) -> str:
    """
    Generate a display friendly message for the response duration, to be added to the footer items.
    """

    return f"Response time: {response_duration:.2f} seconds"


def get_token_usage_message(
    max_tokens: int,
    completion_total_tokens: int,
) -> str:
    """
    Generate a display friendly message for the token usage, to be added to the footer items.
    """

    def get_display_count(tokens: int) -> str:
        # if less than 1k, return the number of tokens
        # if greater than or equal to 1k, return the number of tokens in k
        # use 1 decimal place for k
        # drop the decimal place if the number of tokens in k is a whole number
        if tokens < 1000:
            return str(tokens)
        else:
            tokens_in_k = tokens / 1000
            if tokens_in_k.is_integer():
                return f"{int(tokens_in_k)}k"
            else:
                return f"{tokens_in_k:.1f}k"

    return f"Tokens used: {get_display_count(completion_total_tokens)} of {get_display_count(max_tokens)} ({int(completion_total_tokens / max_tokens * 100)}%)"
