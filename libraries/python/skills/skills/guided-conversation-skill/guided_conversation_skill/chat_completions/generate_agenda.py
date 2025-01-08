"""
`update_agenda` will run a chat completion to create an agenda for the
conversation. The completion will be based on the current state of the
conversation, the artifact, and the resource constraints. The completion will
provide a list of items to be completed sequentially, where the first item
contains everything that will be done in the current turn of the conversation.
The completion will also provide an estimate of the number of turns required to
complete each item. The completion will ensure that the total number of turns
allocated across all items in the updated agenda does not exceed the remaining
turns available. If the completion fails, the function will attempt to fix the
error and generate a new agenda. The function will return the updated agenda and
a boolean indicating whether the conversation is complete. If the completion
fails after multiple attempts, the function will return the current agenda and a
boolean indicating that the conversation is not complete. The function will log
any errors that occur during the completion process.

How do agendas work? See:
https://microsoft.sharepoint.com/:v:/t/NERDAIProgram2/EfRcEA2RSP9DuJhw8AHnAP4B12g__TFV21GOxlZvSR3mEA?e=91Wp9f&nav=eyJwbGF5YmFja09wdGlvbnMiOnt9LCJyZWZlcnJhbEluZm8iOnsicmVmZXJyYWxBcHAiOiJTaGFyZVBvaW50IiwicmVmZXJyYWxNb2RlIjoibWlzIiwicmVmZXJyYWxWaWV3IjoidmlkZW9hY3Rpb25zLXNoYXJlIiwicmVmZXJyYWxQbGF5YmFja1Nlc3Npb25JZCI6ImMzYzUwNTEwLWQ1MzAtNGQyYS1iZGY3LTE2ZGViZTYwNjU4YiJ9fQ%3D%3D
"""

from typing import cast

from guided_conversation_skill.agenda import Agenda, AgendaItem
from guided_conversation_skill.artifact_helpers import get_artifact_for_prompt
from guided_conversation_skill.guide import ConversationGuide
from guided_conversation_skill.message import Conversation
from guided_conversation_skill.resources import (
    ConversationResource,
    ResourceConstraintMode,
    ResourceConstraintUnit,
)
from openai_client import (
    CompletionError,
    create_system_message,
    create_user_message,
    make_completion_args_serializable,
    validate_completion,
)
from pydantic import ValidationError
from skill_library.types import LanguageModel
from traitlets import Any

from ..logging import extra_data, logger
from .fix_agenda_error import fix_agenda_error

GENERATE_AGENDA_TEMPLATE = """
You are a helpful, thoughtful, and meticulous assistant. You are conducting a conversation with a user. Your goal is to complete an artifact as thoroughly as possible by the end of the conversation, and to ensure a smooth experience for the user.

This is the schema of the artifact you are completing:
{{ artifact_schema }}

{% if context %}
Here is some additional context about the conversation:
{{ context }}
{% endif %}

Throughout the conversation, you must abide by these rules:
{{ rules }}

{% if current_state_description %}
Here's a description of the conversation flow:
{{ current_state_description }}

Follow this description, and exercise good judgment about when it is appropriate to deviate.
{% endif %}

You will be provided the history of your conversation with the user up until now and the current state of the artifact. Note that if a required field from the artifact schema is missing from the artifact, it means that the field has not been completed. You need to create an agenda for the remaining conversation given the state of the conversation and the artifact.

How to update the agenda:

- If you need to change your plan for the conversation to make the best use of the remaining turns available to you. Consider how long it usually takes to get the information you need (which is a function of the quality and pace of the user's responses), the number, complexity, and importance of the remaining fields in the artifact, and the number of turns remaining ({{ remaining_resource }}). Based on these factors, you might need to accelerate (e.g. combine several topics) or slow down the conversation (e.g. spread out a topic), in which case you should update the agenda accordingly. Note that skipping an artifact field is NOT a valid way to accelerate the conversation.
- If you do not need to change your plan, just return the list of agenda items as is.
- You must provide an ordered list of items to be completed sequentially, where the first item contains everything you will do in the current turn of the conversation (in addition to updating the agenda). For example, if you choose to send a message to the user asking for their name and medical history, then you would write "ask for name and medical history" as the first item. If you think medical history will take longer than asking for the name, then you would write "complete medical history" as the second item, with an estimate of how many turns you think it will take. Do NOT include items that have already been completed. Items must always represent a conversation topic (corresponding to the "Send message to user" action). Updating the artifact (e.g. "update field X based on the discussion") or terminating the conversation is NOT a valid item.
- The latest agenda was created in the previous turn of the conversation. Even if the total turns in the latest agenda equals the remaining turns, you should still update the agenda if you think the current plan is suboptimal (e.g. the first item was completed, the order of items is not ideal, an item is too broad or not a conversation topic, etc.).
- Each item must have a description and and your best guess for the number of turns required to complete it. Do not provide a range of turns. It is EXTREMELY important that the total turns allocated across all items in the updated agenda (including the first item for the current turn) {{ total_resource_phrase }} Everything in the agenda should be something you expect to complete in the remaining turns - there shouldn't be any optional "buffer" items. It can be helpful to include the cumulative turns allocated for each item in the agenda to ensure you adhere to this rule, e.g. item 1 = 2 turns (cumulative total = 2), item 2 = 4 turns (cumulative total = 6), etc.
- Avoid high-level items like "ask follow-up questions" - be specific about what you need to do.
- Do NOT include wrap-up items such as "review and confirm all information with the user" (you should be doing this throughout the conversation) or "thank the user for their time". Do NOT repeat topics that have already been sufficiently addressed. {{ ample_time_phrase }}

When you determine the conversation is completed, just return an agenda with no items in it.
""".replace("\n\n\n", "\n\n").strip()


def resource_phrase(quantity: float, unit: ResourceConstraintUnit) -> str:
    """
    Get rounded, formatted string for a given quantity and unit (e.g. 1
    turn/second/minute, 20 turns/seconds/minutes).
    """
    quantity = round(quantity)
    s = f"{quantity} {unit.value}"

    # Remove the 's' from if the quantity is 1.
    if quantity == 1:
        return s[:-1]
    else:
        return s


def resource_instructions(resource: ConversationResource) -> str:
    """
    Get the resource instructions for the conversation.

    Note: Assumes we're always using turns as the resource unit.

    Returns:
        str: the resource instructions
    """
    if resource.resource_constraint is None:
        return ""

    is_plural_elapsed = resource.elapsed_units != 1
    is_plural_remaining = resource.remaining_units != 1

    if resource.elapsed_units > 0:
        elapsed_resource_phrase = resource_phrase(resource.elapsed_units, ResourceConstraintUnit.TURNS)
        instructions = (
            f"So far, {elapsed_resource_phrase} {'have' if is_plural_elapsed else 'has'} "
            "elapsed since the conversation began. "
        )
    else:
        instructions = ""

    remaining_resource_phrase = resource_phrase(resource.remaining_units, ResourceConstraintUnit.TURNS)
    if resource.resource_constraint.mode == ResourceConstraintMode.EXACT:
        exact_mode_instructions = (
            f"There {'are' if is_plural_remaining else 'is'} {remaining_resource_phrase} "
            "remaining (including this one) - the conversation will automatically terminate "
            "when 0 turns are left. You should continue the conversation until it is "
            "automatically terminated. This means you should NOT preemptively end the "
            'conversation, either explicitly (by selecting the "End conversation" action) '
            "or implicitly (e.g. by telling the user that you have all required information "
            "and they should wait for the next step). Your goal is not to maximize efficiency "
            "(i.e. complete the artifact as quickly as possible then end the conversation), "
            "but rather to make the best use of ALL remaining turns available to you"
        )

        if is_plural_remaining:
            instructions += (
                f"{exact_mode_instructions}. This will require you to "
                "plan your actions carefully using the agenda: you want to avoid the situation "
                "where you have to pack too many topics into the final turns because you didn't "
                "account for them earlier, or where you've rushed through the conversation and "
                "all fields are completed but there are still many turns left."
            )

        # Special instruction for the final turn (i.e. 1 remaining) in exact mode.
        else:
            instructions += (
                f"{exact_mode_instructions}, including this one. Therefore, you should use this "
                "turn to ask for any remaining information needed to complete the artifact, or, "
                "if the artifact is already completed, continue to broaden/deepen the discussion "
                "in a way that's directly relevant to the artifact. Do NOT indicate to the user "
                "that the conversation is ending."
            )

    elif resource.resource_constraint.mode == ResourceConstraintMode.MAXIMUM:
        instructions += (
            f"You have a maximum of {remaining_resource_phrase} (including this one) left to "
            "complete the conversation. You can decide to terminate the conversation at any point "
            "(including now), otherwise the conversation will automatically terminate when 0 turns "
            "are left. You will need to plan your actions carefully using the agenda: you want to "
            "avoid the situation where you have to pack too many topics into the final turns because "
            "you didn't account for them earlier."
        )
    else:
        logger.error("Invalid resource mode provided.")

    return instructions


def agenda_phrase(agenda: Agenda) -> str:
    """
    Gets a string representation of the agenda for use in an LLM prompt.
    """
    if not agenda.items:
        return "None"
    item_list = "\n".join([
        f"{i + 1}. [{resource_phrase(item.resource, ResourceConstraintUnit.TURNS)}] {item.title}"
        for i, item in enumerate(agenda.items)
    ])
    total_resource = resource_phrase(sum([item.resource for item in agenda.items]), ResourceConstraintUnit.TURNS)
    return item_list + f"\nTotal = {total_resource}"


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
    if (resource_constraint_mode == ResourceConstraintMode.MAXIMUM) and (total_resources > remaining_turns):
        violations.append(
            "The total turns allocated in the agenda "
            f"must not exceed the remaining amount ({remaining_turns}); "
            f"but the current total is {total_resources}."
        )

    # In exact mode if the total resources were not exactly equal to the
    # remaining turns.
    if (resource_constraint_mode == ResourceConstraintMode.EXACT) and (total_resources != remaining_turns):
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


async def generate_agenda(
    language_model: LanguageModel,
    definition: ConversationGuide,
    chat_history: Conversation,
    current_agenda: Agenda,
    artifact: dict[str, Any],
    resource: ConversationResource,
    max_retries: int = 2,
) -> tuple[Agenda, bool]:
    # STEP 1: Generate an updated agenda.

    # If there is a resource constraint and there's more than one turn left,
    # include additional constraint instructions.
    total_resource_phrase = ""
    ample_time_phrase = ""
    if resource.resource_constraint and resource.elapsed_units and resource.remaining_units > 1:
        match resource.resource_constraint.mode:
            case ResourceConstraintMode.MAXIMUM:
                total_resource_phrase = f"does not exceed the remaining turns ({resource.remaining_units})."
            case ResourceConstraintMode.EXACT:
                total_resource_phrase = (
                    f"is equal to the remaining turns ({resource.remaining_units}). Do not leave any turns unallocated."
                )
                ample_time_phrase = (
                    "If you have many turns remaining, instead of including wrap-up items or repeating "
                    "topics, you should include items that increase the breadth and/or depth of the conversation "
                    'in a way that\'s directly relevant to the artifact (e.g. "collect additional details about X", '
                    '"ask for clarification about Y", "explore related topic Z", etc.).'
                )

    completion_args = {
        "model": "gpt-4o",
        "messages": [
            create_system_message(
                GENERATE_AGENDA_TEMPLATE,
                {
                    "ample_time_phrase": ample_time_phrase,
                    "artifact_schema": definition.artifact_schema,
                    "context": definition.conversation_context,
                    "current_state_description": definition.conversation_flow,
                    "remaining_resource": resource.remaining_units,
                    "resource_instructions": resource_instructions(resource),
                    "rules": definition.rules,
                    "total_resource_phrase": total_resource_phrase,
                },
            ),
            create_user_message(
                (
                    "Conversation history:\n"
                    "{{ chat_history }}\n\n"
                    "Latest agenda:\n"
                    "{{ agenda_state }}\n\n"
                    "Current state of the artifact:\n"
                    "{{ artifact_state }}"
                ),
                {
                    "chat_history": str(chat_history),
                    "agenda_state": agenda_phrase(current_agenda),
                    "artifact_state": get_artifact_for_prompt(artifact),
                },
            ),
        ],
        "response_format": Agenda,
    }

    metadata = {}
    logger.debug("Completion call.", extra=extra_data(make_completion_args_serializable(completion_args)))
    metadata["completion_args"] = make_completion_args_serializable(completion_args)
    try:
        completion = await language_model.beta.chat.completions.parse(
            **completion_args,
        )
        validate_completion(completion)
        logger.debug("Completion response.", extra=extra_data({"completion": completion.model_dump()}))
        metadata["completion"] = completion.model_dump()
    except Exception as e:
        completion_error = CompletionError(e)
        metadata["completion_error"] = completion_error.message
        logger.error(
            completion_error.message,
            extra=extra_data({"completion_error": completion_error.body, "metadata": metadata}),
        )
        raise completion_error from e
    else:
        new_agenda = cast(Agenda, completion.choices[0].message.parsed)
        new_agenda.resource_constraint_mode = current_agenda.resource_constraint_mode

    # STEP 2: Validate/fix the updated agenda if necessary.

    previous_attempts = []
    while len(previous_attempts) < max_retries:
        try:
            # Check resource constraints (will raise an error if violated).
            if new_agenda.resource_constraint_mode is not None:
                check_item_constraints(
                    new_agenda.resource_constraint_mode,
                    new_agenda.items,
                    resource.estimate_remaining_turns(),
                )

        except (ValidationError, ValueError) as e:
            # Try again.
            if isinstance(e, ValidationError):
                error_str = "; ".join([e.get("msg") for e in e.errors()])
                error_str = error_str.replace("; Input should be 'Unanswered'", " or input should be 'Unanswered'")
            else:
                error_str = str(e)

            # Add it to our list of previous attempts.
            previous_attempts.append((str(new_agenda.items), error_str))

            # Generate a new agenda.
            logger.info(f"Attempting to fix the agenda error. Attempt {len(previous_attempts)}.")
            llm_formatted_attempts = "\n".join([
                f"Attempt: {attempt}\nError: {error}" for attempt, error in previous_attempts
            ])
            possibly_fixed_agenda = await fix_agenda_error(language_model, llm_formatted_attempts, chat_history)
            if possibly_fixed_agenda is None:
                raise ValueError("Invalid response from the LLM.")
            new_agenda = possibly_fixed_agenda
            continue
        else:
            is_done = True if len(new_agenda.items) == 0 else False
            logger.info("Agenda updated successfully", extra=extra_data(new_agenda))
            return new_agenda, is_done

    logger.error(f"Failed to update agenda after {max_retries} attempts.")

    # Let's keep going anyway.
    return current_agenda, False
