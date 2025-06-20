from typing import Sequence

from ._decorators import log_timing
from ._types import HistoryMessageProtocol, NewTurn, TokenCounts


@log_timing
def high_priority_start_index_for_turn(
    turn: NewTurn,
    messages: Sequence[HistoryMessageProtocol],
    token_counts: TokenCounts,
) -> int:
    """
    Returns the index of the first high priority message.
    """
    if not turn.turn_start_message_id:
        turn.turn_start_message_id = messages[-1].id if messages else None

    start_index = _high_priority_start_index(
        messages=messages,
        token_counts=token_counts,
        high_priority_token_budget=turn.high_priority_token_count,
        turn_start_message_id=turn.turn_start_message_id,
    )

    return start_index


def _high_priority_start_index(
    messages: Sequence[HistoryMessageProtocol],
    token_counts: TokenCounts,
    high_priority_token_budget: int,
    turn_start_message_id: str | None = None,
) -> int:
    """
    Returns the index of the first high priority message.

    High priority starts with the most recent messages that exceed the high priority token budget,
    OR the first message in the turn, whichever is earlier (lower index).
    """

    high_priority_start_index = 0
    turn_start_message_index = len(messages) - 1

    for i in range(len(messages)):
        if turn_start_message_id and messages[i].id == turn_start_message_id:
            turn_start_message_index = i

        if high_priority_start_index == 0:
            token_count = sum(token_counts.openai_message_token_counts[-i - 1 :])
            if token_count > high_priority_token_budget:
                high_priority_start_index = len(messages) - i

    high_priority_start_index = min(high_priority_start_index, turn_start_message_index)

    return high_priority_start_index
