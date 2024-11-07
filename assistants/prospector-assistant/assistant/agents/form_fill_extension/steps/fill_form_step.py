import logging
from dataclasses import dataclass
from pathlib import Path
from textwrap import dedent
from typing import Annotated, Any, Literal

from guided_conversation.utils.resources import ResourceConstraintMode, ResourceConstraintUnit
from openai.types.chat import ChatCompletionMessageParam
from pydantic import BaseModel, Field, create_model
from semantic_workbench_assistant.assistant_app.context import ConversationContext
from semantic_workbench_assistant.assistant_app.protocol import AssistantAppProtocol

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
    app.add_inspector_state_provider(_inspector.state_id, _inspector)


definition = GuidedConversationDefinition(
    rules=[
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
        3. Ask the user to provide one or more files that might contain data relevant to fill out the form. The files can be PDF, TXT, or DOCX.
        4. When asking for files, suggest types of documents that might contain the data.
        5. For each field in the form, check if the data is available in the provided files.
        6. If the data is not available in the files, ask the user for the data.
        7. When the form is filled out, inform the user that you will now generate a document containing the filled form.
    """).strip(),
    context="",
    resource_constraint=ResourceConstraintDefinition(
        quantity=15,
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
    ] = dedent("""
        Given the field definitions below, extract candidate values for these fields from the user provided
        attachment.

        Only include values that are in the provided attachment.
        It is possible that there are multiple candidates for a single field, in which case you should provide
        all the candidates and an explanation for each candidate.

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


@dataclass
class CompleteResult(Result):
    ai_message: str
    artifact: dict


async def execute(
    step_context: Context[FillFormConfig],
    form_filename: str,
    form_fields: list[state.FormField],
) -> IncompleteResult | IncompleteErrorResult | CompleteResult:
    """
    Step: fill out the form with the user
    Approach: Guided conversation
    """
    message = step_context.latest_user_input.message
    debug = {"document-extractions": {}}

    async for attachment in step_context.latest_user_input.attachments:
        if attachment.filename == form_filename:
            continue

        candidate_values, metadata = await _extract(
            llm_config=step_context.llm_config,
            config=step_context.config.extract_config,
            form_fields=form_fields,
            document_content=attachment.content,
        )
        message = f"{message}\n\n" if message else ""
        message = f"{message}{candidate_values.response}\n\nFilename: {attachment.filename}"
        for candidate in candidate_values.fields:
            message += f"\nField id: {candidate.field_id}:\n    Value: {candidate.value}\n    Explanation: {candidate.explanation}"

        debug["document-extractions"][attachment.filename] = metadata

    artifact_type = _form_fields_to_artifact(form_fields)

    definition = step_context.config.definition.model_copy()
    definition.resource_constraint.quantity = int(len(form_fields) * 1.5)
    async with _guided_conversation.engine(
        definition=definition,
        artifact_type=artifact_type,
        state_file_path=_get_state_file_path(step_context.context),
        openai_client=step_context.llm_config.openai_client_factory(),
        openai_model=step_context.llm_config.openai_model,
        context=step_context.context,
        state_id=_inspector.state_id,
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

    if result.is_conversation_over:
        return CompleteResult(
            ai_message="",
            artifact=fill_form_gc_artifact,
            debug=debug,
        )

    return IncompleteResult(message=result.ai_message or "", debug=debug)


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


def _get_state_file_path(context: ConversationContext) -> Path:
    return _guided_conversation.path_for_state(context, "fill_form")


_inspector = FileStateInspector(
    display_name="Fill-Form Guided-Conversation",
    file_path_source=_get_state_file_path,
)


async def _extract(
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
