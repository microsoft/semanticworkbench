from typing import Sequence

from ._decorators import log_timing
from ._types import (
    BudgetDecision,
    HistoryMessageProtocol,
    MessageCollection,
    MessageHistoryBudgetResult,
    OpenAIHistoryMessageParam,
    TokenCounts,
    logger,
)


@log_timing
def abbreviate_messages(
    token_budget: int, message_collection: MessageCollection, before_index: int
) -> Sequence[BudgetDecision]:
    """
    Abbreviates messages, as needed, to reduce token count while retaining essential information.
    Prioritizes the most recent messages and attempts to keep as many intact as possible.
    Abbreviates messages up to the specified `before_index`, leaving the rest unchanged.

    Returns:
        - The resulting budget decisions for each message in the collection.
    """

    messages = message_collection.messages
    token_counts = message_collection.token_counts
    budget_decisions = message_collection.budget_decisions

    result_decisions = list(budget_decisions)

    initial_token_count = token_count_with_budget_applied(
        messages=messages,
        token_counts=token_counts,
        budget_decisions=result_decisions,
    )

    # iterate the messages from oldest to newest, abbreviating until we are within the token budget
    for message_index, message in enumerate(messages):
        if message_index >= before_index:
            # we've reached the index where we stop abbreviating
            break

        if result_decisions[message_index] == BudgetDecision.omitted:
            # this message has already been omitted, skip it
            continue

        current_token_count = token_count_with_budget_applied(
            messages=messages, token_counts=token_counts, budget_decisions=result_decisions
        )

        if current_token_count <= token_budget:
            # we've gone under the token budget. we're done.
            break

        abbreviated_message = message.abbreviated_openai_message
        if abbreviated_message is None:
            # message provider has chosen to omit this message
            result_decisions[message_index] = BudgetDecision.omitted
            continue

        full_message_token_count = token_counts.openai_message_token_counts[message_index]
        abbreviated_message_token_count = token_counts.abbreviated_openai_message_token_counts[message_index]
        if abbreviated_message_token_count > full_message_token_count:
            # only abbreviate if the abbreviated message is smaller than the original
            continue

        if result_decisions[message_index] == BudgetDecision.original:
            result_decisions[message_index] = BudgetDecision.abbreviated

    resulting_token_count = token_count_with_budget_applied(
        messages=messages,
        token_counts=token_counts,
        budget_decisions=result_decisions,
    )
    logger.info(
        "abbreviated %d messages from %d tokens to %d tokens", len(messages), initial_token_count, resulting_token_count
    )

    return result_decisions


@log_timing
def truncate_messages(token_budget: int, message_collection: MessageCollection) -> Sequence[BudgetDecision]:
    """
    Truncates messages to fit within the token budget by removing the oldest messages until the budget is met.
    """
    messages = message_collection.messages
    token_counts = message_collection.token_counts
    budget_decisions = message_collection.budget_decisions

    result_decisions = list(budget_decisions)

    initial_token_count = token_count_with_budget_applied(
        messages=messages,
        token_counts=token_counts,
        budget_decisions=result_decisions,
    )

    # iterate the messages from oldest to newest, truncating until we are within the token budget
    current_token_count = 0
    for message_index in range(len(messages)):
        current_token_count = token_count_with_budget_applied(
            messages=messages,
            token_counts=token_counts,
            budget_decisions=result_decisions,
        )

        if current_token_count <= token_budget:
            # we've gone under the token budget. we're done.
            break

        result_decisions[message_index] = BudgetDecision.omitted

    resulting_token_count = token_count_with_budget_applied(
        messages=messages,
        token_counts=token_counts,
        budget_decisions=result_decisions,
    )
    logger.info(
        "truncated %d messages from %d tokens to %d tokens", len(messages), initial_token_count, resulting_token_count
    )
    if resulting_token_count == 0 and len(messages) > 0:
        logger.warning(
            "no messages fit within the token budget of %d tokens; final message token count: %d",
            token_budget,
            current_token_count,
        )

    return result_decisions


def token_count_with_budget_applied(
    messages: Sequence[HistoryMessageProtocol],
    token_counts: TokenCounts,
    budget_decisions: Sequence[BudgetDecision],
) -> int:
    """
    Counts the tokens in the messages, applying the budget decisions to determine the effective token count.
    """

    token_count = 0
    for message_index, (message, decision) in enumerate(zip(messages, budget_decisions)):
        match decision:
            case BudgetDecision.omitted:
                # message is omitted, do not include it in the count
                continue
            case BudgetDecision.abbreviated:
                # message is abbreviated, use the abbreviated token count
                if message.abbreviated_openai_message is None:
                    # if the abbreviated message is None, it means the message was omitted
                    continue
                # use the abbreviated token count
                token_count += token_counts.abbreviated_openai_message_token_counts[message_index]
            case BudgetDecision.original:
                # message is original, use the full token count
                token_count += token_counts.openai_message_token_counts[message_index]

    return token_count


def apply_budget_decisions(
    messages: Sequence[HistoryMessageProtocol],
    decisions: Sequence[BudgetDecision],
) -> MessageHistoryBudgetResult:
    """
    Applies budget decisions to the messages, returning a list of messages that fit within the budget.
    If a message is abbreviated, it will be replaced with its abbreviated version.
    If a message is omitted, it will not be included in the result.

    Returns:
        A list of messages with the budget decisions applied.
    """
    oldest_retained_message_id: str | None = None
    result_messages: list[OpenAIHistoryMessageParam] = []

    for message, decision in zip(messages, decisions):
        match decision:
            case BudgetDecision.omitted:
                # message is omitted, do not include it in the result
                pass
            case BudgetDecision.abbreviated:
                # message is abbreviated, include the abbreviated version
                if message.abbreviated_openai_message is not None:
                    if oldest_retained_message_id is None:
                        oldest_retained_message_id = message.id
                    result_messages.append(message.abbreviated_openai_message)
            case BudgetDecision.original:
                # message is original, include the full version
                result_messages.append(message.openai_message)
                if oldest_retained_message_id is None:
                    oldest_retained_message_id = message.id

    return MessageHistoryBudgetResult(
        messages=result_messages,
        oldest_message_id=oldest_retained_message_id,
    )
