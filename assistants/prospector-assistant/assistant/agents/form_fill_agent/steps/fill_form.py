import logging
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Literal

from guided_conversation.utils.resources import ResourceConstraintMode, ResourceConstraintUnit
from pydantic import Field, create_model
from semantic_workbench_assistant.assistant_app.context import ConversationContext

from .. import gce_config, state
from ..inspector import FileStateInspector
from ..step import Context, IncompleteErrorResult, IncompleteResult, Result
from . import gce

logger = logging.getLogger(__name__)


definition = gce_config.GuidedConversationDefinition(
    rules=[
        "For fields that are not in the provided files, collect the data from the user through conversation.",
        "When providing options for a multiple choice field, provide the options in a numbered-list, so the user can refer to them by number.",
        "When listing anything other than options, like document types, provide them in a bulleted list for improved readability.",
        "When updating the agenda, the data-collection for each form field must be in a separate step.",
        "Terminate conversation if inappropriate content is requested.",
    ],
    conversation_flow="""
1. Inform the user that we've received the form and determined the fields in the form.
2. Inform the user that our goal is help them fill out the form.
3. Ask the user to provide one or more files that might contain data relevant to fill out the form. The files can be PDF, TXT, or DOCX.
4. When asking for files, suggest types of documents that might contain the data.
5. For each field in the form, check if the data is available in the provided files.
6. If the data is not available in the files, ask the user for the data.
7. When asking for data to fill the form, ask for a single piece of information at a time.
8. When the form is filled out, inform the user that you will now generate a document containing the filled form.
""",
    context="",
    resource_constraint=gce_config.ResourceConstraintDefinition(
        quantity=15,
        unit=ResourceConstraintUnit.TURNS,
        mode=ResourceConstraintMode.MAXIMUM,
    ),
)


@dataclass
class CompleteResult(Result):
    ai_message: str
    artifact: dict


def get_state_file_path(context: ConversationContext) -> Path:
    return gce.path_for_guided_conversation_state(context, "fill_form")


async def execute(
    step_context: Context[gce_config.GuidedConversationDefinition],
    latest_user_message: str | None,
    form_fields: list[state.FormField],
) -> IncompleteResult | IncompleteErrorResult | CompleteResult:
    """
    Step: fill out the form with the user
    Approach: Guided conversation
    """
    message_with_attachments = await gce.message_with_recent_attachments(
        step_context.context, latest_user_message, step_context.get_attachment_messages
    )

    artifact_type = _form_fields_to_artifact(form_fields)

    definition = step_context.config.model_copy()
    definition.resource_constraint.quantity = int(len(form_fields) * 1.5)
    async with gce.guided_conversation_with_state(
        definition=definition,
        artifact_type=artifact_type,
        state_file_path=get_state_file_path(step_context.context),
        openai_client=step_context.llm_config.openai_client_factory(),
        openai_model=step_context.llm_config.openai_model,
    ) as guided_conversation:
        try:
            result = await guided_conversation.step_conversation(message_with_attachments)
        except Exception as e:
            logger.exception("failed to execute guided conversation")
            return IncompleteErrorResult(
                error_message=f"Failed to execute guided conversation: {e}",
                debug={"error": str(e)},
            )

        logger.info("guided-conversation result: %s", result)

        fill_form_gc_artifact = guided_conversation.artifact.artifact.model_dump(mode="json")
        logger.info("guided-conversation artifact: %s", guided_conversation.artifact)

    if result.is_conversation_over:
        return CompleteResult(
            ai_message="",
            artifact=fill_form_gc_artifact,
            debug={"artifact": fill_form_gc_artifact},
        )

    return IncompleteResult(
        ai_message=result.ai_message or "",
        debug={"artifact": fill_form_gc_artifact},
    )


def _form_fields_to_artifact(form_fields: list[state.FormField]):
    field_definitions: dict[str, tuple[Any, Any]] = {}
    required_fields = []
    for field in form_fields:
        if field.required:
            required_fields.append(field.id)

        match field.type:
            case "string":
                field_definitions[field.id] = (str, Field(title=field.name, description=field.description))

            case "bool":
                field_definitions[field.id] = (bool, Field(title=field.name, description=field.description))

            case "multiple_choice":
                field_definitions[field.id] = (
                    Literal[tuple(field.options)],
                    Field(title=field.name, description=field.description),
                )

    return create_model(
        "FilledFormArtifact",
        **field_definitions,  # type: ignore
    )  # type: ignore


FillFormGuidedConversationStateInspector = FileStateInspector(
    display_name="Fill Form Guided Conversation State",
    file_path_source=get_state_file_path,
)
