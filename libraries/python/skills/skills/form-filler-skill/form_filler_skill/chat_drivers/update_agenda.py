import logging

from form_filler_skill.agenda import Agenda, AgendaItem
from form_filler_skill.message import Conversation
from form_filler_skill.resources import (
    GCResource,
    ResourceConstraintMode,
    ResourceConstraintUnit,
    format_resource,
)
from openai import AsyncAzureOpenAI, AsyncOpenAI
from pydantic import ValidationError
from skill_library.run_context import RunContext

from .fix_agenda_error import fix_agenda_error

logger = logging.getLogger(__name__)


async def update_agenda(
    context: RunContext,
    openai_client: AsyncOpenAI | AsyncAzureOpenAI,
    items: str,
    chat_history: Conversation,
    agenda: Agenda,
    resource: GCResource,
) -> bool:
    previous_attempts = []
    while True:
        try:
            # Pydantic type validation.
            agenda.items = items  # type: ignore

            # Check resource constraints.
            if agenda.resource_constraint_mode is not None:
                check_item_constraints(
                    agenda.resource_constraint_mode,
                    agenda.items,
                    resource.estimate_remaining_turns(),
                )

            logger.info(f"Agenda updated successfully: {get_agenda_for_prompt(agenda)}")
            return True

        except (ValidationError, ValueError) as e:
            # If we have reached the maximum number of retries return a failure.
            if len(previous_attempts) >= agenda.max_agenda_retries:
                logger.warning(
                    f"Failed to update agenda after {agenda.max_agenda_retries} attempts."
                )
                return False

            # Otherwise, get an error string.
            if isinstance(e, ValidationError):
                error_str = "; ".join([e.get("msg") for e in e.errors()])
                error_str = error_str.replace(
                    "; Input should be 'Unanswered'", " or input should be 'Unanswered'"
                )
            else:
                error_str = str(e)

            # Add it to our list of previous attempts.
            previous_attempts.append((str(items), error_str))

            # And try again.
            logger.info(f"Attempting to fix the agenda error. Attempt {len(previous_attempts)}.")
            llm_formatted_attempts = "\n".join([
                f"Attempt: {attempt}\nError: {error}" for attempt, error in previous_attempts
            ])
            response = await fix_agenda_error(
                context, openai_client, llm_formatted_attempts, chat_history
            )

            # Now, update the items with the corrected agenda and try to
            # validate again.
            items = response.message or ""


def check_item_constraints(
    resource_constraint_mode: ResourceConstraintMode,
    items: list[AgendaItem],
    remaining_turns: int,
) -> None:
    """
    Validates if any constraints were violated while performing the agenda
    update.
    """
    # The total, proposed allocation of resources.
    total_resources = sum([item.resource for item in items])

    violations = []
    # In maximum mode, the total resources should not exceed the remaining
    # turns.
    if (resource_constraint_mode == ResourceConstraintMode.MAXIMUM) and (
        total_resources > remaining_turns
    ):
        violations.append(
            "The total turns allocated in the agenda "
            f"must not exceed the remaining amount ({remaining_turns}); "
            f"but the current total is {total_resources}."
        )

    # In exact mode if the total resources were not exactly equal to the
    # remaining turns.
    if (resource_constraint_mode == ResourceConstraintMode.EXACT) and (
        total_resources != remaining_turns
    ):
        violations.append(
            "The total turns allocated in the agenda "
            f"must equal the remaining amount ({remaining_turns}); "
            f"but the current total is {total_resources}."
        )

    # Check if any item has a resource value of 0.
    if any(item.resource <= 0 for item in items):
        violations.append("All items must have a resource value greater than 0.")

    # Raise an error if any violations were found.
    if len(violations) > 0:
        logger.debug(f"Agenda update failed due to the following violations: {violations}.")
        raise ValueError(" ".join(violations))


def get_agenda_for_prompt(agenda: Agenda) -> str:
    """
    Gets a string representation of the agenda for use in an LLM prompt.
    """
    agenda_json = agenda.model_dump()
    agenda_items = agenda_json.get("items", [])
    if len(agenda_items) == 0:
        return "None"
    agenda_str = "\n".join([
        f"{i + 1}. [{format_resource(item['resource'], ResourceConstraintUnit.TURNS)}] {item['title']}"
        for i, item in enumerate(agenda_items)
    ])
    total_resource = format_resource(
        sum([item["resource"] for item in agenda_items]), ResourceConstraintUnit.TURNS
    )
    agenda_str += f"\nTotal = {total_resource}"
    return agenda_str
