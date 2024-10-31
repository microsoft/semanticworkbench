from typing import Any, Literal

from guided_conversation.utils.resources import ResourceConstraintMode, ResourceConstraintUnit
from pydantic import Field, create_model

from .definition import GuidedConversationDefinition, ResourceConstraintDefinition
from .extract_form_fields import FormFields


def form_fields_to_artifact(form_fields: FormFields):
    field_definitions: dict[str, tuple[Any, Any]] = {}
    required_fields = []
    for field in form_fields.fields:
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


definition = GuidedConversationDefinition(
    rules=[
        "Request the user to provide one or more files that might provide the data required to fill the form.",
        "For fields that are not in the provided files, collect the data from the user through conversation.",
        "When providing options for a multiple choice field, provide the options in a numbered-list, so the user can refer to them by number.",
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
8. Inform the user when the form is filled out.
""",
    context="",
    resource_constraint=ResourceConstraintDefinition(
        quantity=15,
        unit=ResourceConstraintUnit.MINUTES,
        mode=ResourceConstraintMode.MAXIMUM,
    ),
)
