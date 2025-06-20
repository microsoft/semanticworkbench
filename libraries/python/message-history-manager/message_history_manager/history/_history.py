from typing import Sequence

from message_history_manager.history._decorators import log_timing

from . import _budget as budget
from . import _prioritize as prioritize
from ._types import (
    BudgetDecision,
    HistoryMessageProtocol,
    HistoryMessageProvider,
    MessageCollection,
    NewTurn,
    OpenAIHistoryMessageParam,
    TokenCounter,
    TokenCounts,
    logger,
)


@log_timing
async def apply_budget_to_history_messages(
    turn: NewTurn,
    token_budget: int,
    token_counter: TokenCounter,
    message_provider: HistoryMessageProvider,
) -> Sequence[OpenAIHistoryMessageParam]:
    """
    Retrieves the history messages for a given turn, applying message content abbreviation and truncation
    to guarantee that the total token count of the messages fits within the specified token budget.
    """
    messages = await message_provider(after_id=None)

    logger.info("get_history_messages received %d messages to process", len(messages))

    message_collection = MessageCollection(
        messages=messages,
        # count all tokens for all messages - this will be used by the various budgeting functions
        token_counts=count_tokens(messages=messages, token_counter=token_counter),
        # initialize budget decisions for all messages
        budget_decisions=[BudgetDecision.original for _ in range(len(messages))],
    )

    message_token_count = sum(message_collection.token_counts.openai_message_token_counts)

    logger.info(
        "messages: %d, token count: %d, token budget: %d",
        len(message_collection.messages),
        message_token_count,
        token_budget,
    )

    # get the start of the high priority messages for this turn
    high_priority_start_index = prioritize.high_priority_start_index_for_turn(
        turn=turn,
        messages=message_collection.messages,
        token_counts=message_collection.token_counts,
    )

    # 1. apply abbreviation up to the high priority start index
    message_collection.budget_decisions = budget.abbreviate_messages(
        token_budget=token_budget,
        message_collection=message_collection,
        before_index=high_priority_start_index,
    )

    if is_within_budget(
        token_budget=token_budget,
        message_collection=message_collection,
    ):
        return get_resulting_messages(message_collection=message_collection)

    # 2. still over budget, truncate
    message_collection.budget_decisions = budget.truncate_messages(
        token_budget=token_budget,
        message_collection=message_collection,
    )

    return get_resulting_messages(message_collection=message_collection)


def is_within_budget(
    token_budget: int,
    message_collection: MessageCollection,
) -> bool:
    """Checks if the total token count of messages in the collection is within the specified token budget."""
    token_count = budget.token_count_with_budget_applied(
        messages=message_collection.messages,
        token_counts=message_collection.token_counts,
        budget_decisions=message_collection.budget_decisions,
    )
    return token_count <= token_budget


def get_resulting_messages(message_collection: MessageCollection) -> Sequence[OpenAIHistoryMessageParam]:
    """
    Applies the budget decisions to the messages in the collection and returns the resulting messages.

    Raises a ValueError if all messages are omitted (ie. zero messages could fit in the budget).
    """
    result_messages = budget.apply_budget_decisions(
        messages=message_collection.messages, decisions=message_collection.budget_decisions
    )

    result_messages = pair_and_order_tool_messages(result_messages)

    if len(message_collection.messages) > 0 and not result_messages:
        raise ValueError(
            "no messages fit within the token budget; "
            "consider increasing the token budget or limiting the size of messages"
        )

    return result_messages


def count_tokens(messages: Sequence[HistoryMessageProtocol], token_counter: TokenCounter) -> TokenCounts:
    """
    Counts the tokens in the messages, both for the original OpenAI message and the abbreviated version.
    """
    original_token_counts = [token_counter([msg.openai_message]) for msg in messages]
    abbreviated_token_counts = [
        token_counter([msg.abbreviated_openai_message]) if msg.abbreviated_openai_message else 0 for msg in messages
    ]
    return TokenCounts(
        openai_message_token_counts=original_token_counts,
        abbreviated_openai_message_token_counts=abbreviated_token_counts,
    )


def pair_and_order_tool_messages(messages: Sequence[OpenAIHistoryMessageParam]) -> Sequence[OpenAIHistoryMessageParam]:
    """
    Pairs tool calls with their results and orders them correctly in the message history.
    """
    tool_call_to_position: dict[str, int] = {}
    tool_result_to_position: dict[str, int] = {}

    messages_indices_to_omit = set[int]()

    # first, identify all tool calls and tool results and their positions
    for i, message in enumerate(messages):
        match message:
            case {"role": "assistant", "tool_calls": tool_calls}:
                for tool_call in tool_calls:
                    tool_call_to_position[tool_call["id"]] = i

            case {"role": "tool", "tool_call_id": tool_call_id}:
                # omit duplicate tool (result) messages for the same tool call ID
                if tool_call_id in tool_result_to_position:
                    logger.warning(
                        "multiple tool messages for the same tool call ID %s found; omitting message at index %d",
                        tool_call_id,
                        i,
                    )
                    messages_indices_to_omit.add(i)
                    continue

                tool_result_to_position[tool_call_id] = i

    # omit assistant messages that have tool calls without corresponding tool messages
    assistant_positions_with_incomplete_tool_calls = set[int]()
    for tool_call_id, position in tool_call_to_position.items():
        if tool_call_id in tool_result_to_position:
            continue

        logger.warning(
            "assistant message at index %d has a tool call ID %s that does not have a corresponding tool message; omitting the assistant message",
            position,
            tool_call_id,
        )
        assistant_positions_with_incomplete_tool_calls.add(position)

    messages_indices_to_omit.update(assistant_positions_with_incomplete_tool_calls)

    # omit tool messages that don't have corresponding assistant messages
    for tool_call_id, position in tool_result_to_position.items():
        if tool_call_id in tool_call_to_position:
            continue

        logger.warning(
            "tool message at index %d has a tool call ID %s that does not have a corresponding assistant message; omitting the tool message",
            position,
            tool_call_id,
        )
        messages_indices_to_omit.add(position)

    tool_result_position_indices = set(tool_result_to_position.values())
    corrected_messages = []

    # build the corrected message list, omitting the messages that were marked for omission, and with
    # tool result messages placed immediately after their corresponding assistant messages
    for i, message in enumerate(messages):
        if i in messages_indices_to_omit:
            continue

        if i in tool_result_position_indices:
            continue

        match message:
            case {"role": "assistant", "tool_calls": tool_calls}:
                corrected_messages.append(message)

                # place corresponding tool result messages immediately after the assistant message
                for tool_call in tool_calls:
                    tool_result_position = tool_result_to_position.get(tool_call["id"])
                    if tool_result_position is not None:
                        corrected_messages.append(messages[tool_result_position])

            case _:
                corrected_messages.append(message)

    return corrected_messages
