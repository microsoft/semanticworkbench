import logging
from contextlib import asynccontextmanager
from dataclasses import dataclass
from pathlib import Path
from textwrap import dedent
from typing import Annotated, Any, AsyncIterator, Literal, Optional

from guided_conversation.utils.resources import ResourceConstraintMode, ResourceConstraintUnit
from openai.types.chat import ChatCompletionMessageParam
from pydantic import BaseModel, ConfigDict, Field, create_model
from semantic_workbench_assistant.assistant_app.context import ConversationContext, storage_directory_for_context
from semantic_workbench_assistant.assistant_app.protocol import AssistantAppProtocol
from semantic_workbench_assistant.config import UISchema

from .. import state
from ..inspector import FileStateInspector
from . import _guided_conversation, _llm
from .types import (
    Context,
    GuidedConversationDefinition,
    IncompleteErrorResult,
    IncompleteResult,
    LLMConfig,
    ResourceConstraintDefinition,
    Result,
)

logger = logging.getLogger(__name__)


def extend(app: AssistantAppProtocol) -> None:
    app.add_inspector_state_provider(_guided_conversation_inspector.state_id, _guided_conversation_inspector)
    app.add_inspector_state_provider(_populated_form_state_inspector.state_id, _populated_form_state_inspector)


definition = GuidedConversationDefinition(
    rules=[
        "When kicking off the conversation, do not greet the user with Hello or other greetings.",
        "For fields that are not in the provided files, collect the data from the user through conversation.",
        "When providing options for a multiple choice field, provide the options in a numbered-list, so the user can refer to them by number.",
        "When listing anything other than options, like document types, provide them in a bulleted list for improved readability.",
        "When updating the agenda, the data-collection for each form field must be in a separate step.",
        "When asking for data to fill the form, always ask for a single piece of information at a time. Never ask for multiple pieces of information in a single prompt, ex: 'Please provide field Y, and additionally, field X'.",
        "Terminate conversation if inappropriate content is requested.",
    ],
    conversation_flow=dedent("""
        1. Inform the user that we've received the form and determined the fields in the form.
        2. Inform the user that our goal is help them fill out the form.
        3. Ask the user to provide one or more files that might contain data relevant to fill out the form. The files can be PDF, TXT, DOCX, or PNG.
        4. When asking for files, suggest types of documents that might contain the data.
        5. For each field in the form, check if the data is available in the provided files.
        6. If the data is not available in the files, ask the user for the data.
        7. When the form is filled out, inform the user that you will now generate a document containing the filled form.
    """).strip(),
    context="",
    resource_constraint=ResourceConstraintDefinition(
        quantity=1000,
        unit=ResourceConstraintUnit.TURNS,
        mode=ResourceConstraintMode.MAXIMUM,
    ),
)


class ExtractCandidateFieldValuesConfig(BaseModel):
    instruction: Annotated[
        str,
        Field(
            title="Instruction",
            description="The instruction for extracting candidate form-field values from an uploaded file",
        ),
        UISchema(widget="textarea"),
    ] = dedent("""
        Given the field definitions below, extract candidate values for these fields from the user provided
        attachment.

        Only include values that are in the provided attachment.
        It is possible that there are multiple candidates for a single field, in which case you should provide
        all the candidates and an explanation for each candidate.

        For example, if their is a field for an individual's name, 'name', and there are multiple names in the
        attachment, you should provide all the names in the attachment as candidates for the 'name' field.

        Also, if their are multiple fields for individual's names in the form, 'name_one' and 'name_two', and
        there are one or more names in the attachment, you should provide all the names in the attachment as
        candidates for the 'name_one' and 'name_two' field.

        Field definitions:
        {{form_fields}}
    """)


class FillFormConfig(BaseModel):
    extract_config: ExtractCandidateFieldValuesConfig = ExtractCandidateFieldValuesConfig()
    definition: GuidedConversationDefinition = definition


class FieldValueCandidate(BaseModel):
    field_id: str = Field(description="The ID of the field that the value is a candidate for.")
    value: str = Field(description="The value from the document for this field.")
    explanation: str = Field(description="The explanation of why this value is a candidate for the field.")


class FieldValueCandidates(BaseModel):
    response: str = Field(description="The natural language response to send to the user.")
    fields: list[FieldValueCandidate] = Field(description="The fields in the form.")


class FieldValueCandidatesFromDocument(BaseModel):
    filename: str
    candidates: FieldValueCandidates


class FillFormState(BaseModel):
    populated_form_markdown: str = "(The form has not yet been provided)"


@dataclass
class CompleteResult(Result):
    message: str
    artifact: dict
    populated_form_markdown: str


async def execute(
    step_context: Context[FillFormConfig],
    form_filename: str,
    form: state.Form,
) -> IncompleteResult | IncompleteErrorResult | CompleteResult:
    """
    Step: fill out the form with the user through conversation and pulling values from uploaded attachments.
    Approach: Guided conversation / direct chat-completion (for document extraction)
    """

    def fields_for(section: state.Section) -> list[state.FormField]:
        form_fields = section.fields.copy()
        for sub_section in section.sections:
            form_fields.extend(fields_for(sub_section))
        return form_fields

    form_fields = fields_for(form)

    debug = {}

    message_part, message_debug = await _candidate_values_from_attachments_as_message_part(
        step_context, form_filename, form_fields
    )

    message = "\n".join((step_context.latest_user_input.message or "", message_part))
    if message_debug:
        debug["document-extractions"] = message_debug

    artifact_type = _form_fields_to_artifact_basemodel(form_fields)

    async with _guided_conversation.engine(
        definition=step_context.config.definition,
        artifact_type=artifact_type,
        state_file_path=_get_guided_conversation_state_file_path(step_context.context),
        openai_client=step_context.llm_config.openai_client_factory(),
        openai_model=step_context.llm_config.openai_model,
        context=step_context.context,
        state_id=_guided_conversation_inspector.state_id,
    ) as gce:
        try:
            result = await gce.step_conversation(message)
        except Exception as e:
            logger.exception("failed to execute guided conversation")
            return IncompleteErrorResult(
                message=f"Failed to execute guided conversation: {e}",
                debug={"error": str(e)},
            )

        debug["guided-conversation"] = gce.to_json()

        logger.info("guided-conversation result: %s", result)

        fill_form_gc_artifact = gce.artifact.artifact.model_dump(mode="json")
        logger.info("guided-conversation artifact: %s", gce.artifact)

    populated_form_markdown = _generate_populated_form(
        form=form,
        populated_fields=fill_form_gc_artifact,
    )

    async with step_state(step_context.context) as current_state:
        current_state.populated_form_markdown = populated_form_markdown

        if result.is_conversation_over:
            return CompleteResult(
                message=current_state.populated_form_markdown,
                artifact=fill_form_gc_artifact,
                populated_form_markdown=current_state.populated_form_markdown,
                debug=debug,
            )

        return IncompleteResult(message=result.ai_message or "", debug=debug)


async def _candidate_values_from_attachments_as_message_part(
    step_context: Context[FillFormConfig], form_filename: str, form_fields: list[state.FormField]
) -> tuple[str, dict[str, Any]]:
    """Extract candidate values from the attachments, using chat-completion, and return them as a message part."""

    debug_per_file = {}
    attachment_candidate_value_parts = []
    async with step_context.context.set_status("inspecting attachments ..."):
        async for attachment in step_context.latest_user_input.attachments:
            if attachment.filename == form_filename:
                continue

            candidate_values, metadata = await _extract_field_candidates(
                llm_config=step_context.llm_config,
                config=step_context.config.extract_config,
                form_fields=form_fields,
                document_content=attachment.content,
            )

            message_part = _candidate_values_to_message_part(attachment.filename, candidate_values)
            attachment_candidate_value_parts.append(message_part)

            debug_per_file[attachment.filename] = metadata

    return "\n".join(attachment_candidate_value_parts), debug_per_file


def _candidate_values_to_message_part(filename: str, candidate_values: FieldValueCandidates) -> str:
    """Build a message part from the candidate values extracted from a document."""
    header = dedent(f"""===
        Filename: *{filename}*
        {candidate_values.response}
    """)

    fields = []
    for candidate in candidate_values.fields:
        fields.append(
            dedent(f"""
            Field id: {candidate.field_id}:
                Value: {candidate.value}
                Explanation: {candidate.explanation}""")
        )

    return "\n".join((header, *fields))


def _form_fields_to_artifact_basemodel(form_fields: list[state.FormField]):
    """Create a BaseModel for the filled-form-artifact based on the form fields."""
    field_definitions: dict[str, tuple[Any, Any]] = {}
    required_fields = []
    for field in form_fields:
        if field.required:
            required_fields.append(field.id)

        match field.type:
            case state.FieldType.text | state.FieldType.signature | state.FieldType.date:
                field_type = str

            case state.FieldType.text_list:
                field_type = list[str]

            case state.FieldType.currency:
                field_type = float

            case state.FieldType.multiple_choice:
                match field.option_selections_allowed:
                    case state.AllowedOptionSelections.one:
                        field_type = Literal[tuple(field.options)]

                    case state.AllowedOptionSelections.many:
                        field_type = list[Literal[tuple(field.options)]]

                    case _:
                        raise ValueError(f"Unsupported option_selections_allowed: {field.option_selections_allowed}")

            case _:
                raise ValueError(f"Unsupported field type: {field.type}")

        if not field.required:
            field_type = Optional[field_type]

        field_definitions[field.id] = (field_type, Field(title=field.name, description=field.description))

    return create_model(
        "FilledFormArtifact",
        __config__=ConfigDict(json_schema_extra={"required": required_fields}),
        **field_definitions,  # type: ignore
    )


def _get_guided_conversation_state_file_path(context: ConversationContext) -> Path:
    return _guided_conversation.path_for_state(context, "fill_form")


_guided_conversation_inspector = FileStateInspector(
    display_name="Debug: Fill-Form Guided-Conversation",
    file_path_source=_get_guided_conversation_state_file_path,
)


def _get_step_state_file_path(context: ConversationContext) -> Path:
    return storage_directory_for_context(context, "fill_form_state.json")


def project_populated_form(state: dict) -> str:
    return state.get("populated_form_markdown") or ""


_populated_form_state_inspector = FileStateInspector(
    display_name="Populated Form",
    file_path_source=_get_step_state_file_path,
    projector=project_populated_form,
)


async def _extract_field_candidates(
    llm_config: LLMConfig,
    config: ExtractCandidateFieldValuesConfig,
    form_fields: list[state.FormField],
    document_content: str,
) -> tuple[FieldValueCandidates, dict[str, Any]]:
    class _SerializationModel(BaseModel):
        fields: list[state.FormField]

    messages: list[ChatCompletionMessageParam] = [
        {
            "role": "system",
            "content": config.instruction.replace(
                "{{form_fields}}", _SerializationModel(fields=form_fields).model_dump_json(indent=4)
            ),
        },
        {
            "role": "user",
            "content": document_content,
        },
    ]

    return await _llm.structured_completion(
        llm_config=llm_config,
        messages=messages,
        response_model=FieldValueCandidates,
    )


def _generate_populated_form(
    form: state.Form,
    populated_fields: dict,
) -> str:
    def field_value(field_id: str) -> str | list[str]:
        value = populated_fields.get(field_id) or ""
        if value == "Unanswered":
            return ""
        if value == "null":
            return ""
        if isinstance(value, list):
            return value
        return value

    def field_values(fields: list[state.FormField]) -> str:
        markdown_fields: list[str] = []

        for field in fields:
            value = field_value(field.id)

            markdown_fields.append("_" * 20)
            markdown_fields.append(f"{field.name}:")
            if field.description:
                markdown_fields.append(f'<span style="font-size: 0.75em;opacity:0.6;">ℹ️ {field.description}</span>\n')

            match field.type:
                case (
                    state.FieldType.text
                    | state.FieldType.signature
                    | state.FieldType.date
                    | state.FieldType.text_list
                    | state.FieldType.currency
                ):
                    match value:
                        case str():
                            markdown_fields.append(value)

                        case int() | float():
                            markdown_fields.append(str(value))

                        case list():
                            for item in value:
                                markdown_fields.append(f"- {item}")

                case state.FieldType.multiple_choice:
                    for option in field.options:
                        if option == value:
                            markdown_fields.append(f"- [x] {option}\n")
                            continue
                        markdown_fields.append(f"- [ ] {option}\n")

                case _:
                    raise ValueError(f"Unsupported field type: {field.type}")

        return "\n\n".join(markdown_fields)

    def for_section(level: int, section: state.Section) -> str:
        sections = (for_section(level + 1, section) for section in section.sections)
        return "\n".join((
            f"{'#' * level} {section.title}",
            section.description,
            section.instructions,
            field_values(section.fields),
            *sections,
        ))

    return "\n".join((
        "```markdown",
        for_section(1, form),
        "```",
    ))


@asynccontextmanager
async def step_state(context: ConversationContext) -> AsyncIterator[FillFormState]:
    state_file_path = _get_step_state_file_path(context)
    step_state = state.read_model(state_file_path, FillFormState) or FillFormState()
    async with context.state_updated_event_after(_populated_form_state_inspector.state_id, focus_event=True):
        yield step_state
        state.write_model(state_file_path, step_state)
