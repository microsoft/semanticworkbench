from contextlib import asynccontextmanager
from contextvars import ContextVar
from enum import StrEnum
from pathlib import Path
from typing import AsyncIterator

from pydantic import BaseModel, Field
from semantic_workbench_assistant.assistant_app.context import ConversationContext, storage_directory_for_context
from semantic_workbench_assistant.storage import read_model, write_model

from .inspector import FileStateInspector


class FieldType(StrEnum):
    text = "text"
    text_list = "text_list"
    currency = "currency"
    date = "date"
    signature = "signature"
    multiple_choice = "multiple_choice"


class AllowedOptionSelections(StrEnum):
    one = "one"
    """One of the options can be selected."""
    many = "many"
    """One or more of the options can be selected."""


class FormField(BaseModel):
    id: str = Field(description="The descriptive, unique identifier of the field as a snake_case_english_string.")
    name: str = Field(description="The name of the field.")
    description: str = Field(description="The description of the field.")
    type: FieldType = Field(description="The type of the field.")
    options: list[str] = Field(description="The options for multiple choice fields.")
    option_selections_allowed: AllowedOptionSelections | None = Field(
        description="The number of options that can be selected for multiple choice fields."
    )
    required: bool = Field(
        description="Whether the field is required or not. False indicates the field is optional and can be left blank."
    )


class Section(BaseModel):
    title: str = Field(description="The title of the section if one is provided on the form.")
    description: str = Field(description="The description of the section if one is provided on the form.")
    instructions: str = Field(description="The instructions for the section if they are provided on the form.")
    fields: list[FormField] = Field(description="The fields of the section.")


class Form(BaseModel):
    title: str = Field(description="The title of the form.")
    description: str = Field(description="The description of the form if one is provided on the form.")
    instructions: str = Field(description="The instructions for the form if they are provided on the form.")
    fields: list[FormField] = Field(description="The fields of the form, if there are any at the top level.")
    sections: list[Section] = Field(description="The sections of the form, if there are any.")


class FormFillExtensionMode(StrEnum):
    acquire_form_step = "acquire_form"
    extract_form_fields = "extract_form_fields"
    fill_form_step = "fill_form"
    conversation_over = "conversation_over"


class FormFillExtensionState(BaseModel):
    mode: FormFillExtensionMode = FormFillExtensionMode.acquire_form_step
    form_filename: str = ""
    extracted_form: Form | None = None
    populated_form_markdown: str = ""
    fill_form_gc_artifact: dict | None = None


def path_for_state(context: ConversationContext) -> Path:
    return storage_directory_for_context(context) / "state.json"


current_state = ContextVar[FormFillExtensionState | None]("current_state", default=None)


@asynccontextmanager
async def extension_state(context: ConversationContext) -> AsyncIterator[FormFillExtensionState]:
    """
    Context manager that provides the agent state, reading it from disk, and saving back
    to disk after the context manager block is executed.
    """
    state = current_state.get()
    if state is not None:
        yield state
        return

    async with context.state_updated_event_after(inspector.state_id):
        state = read_model(path_for_state(context), FormFillExtensionState) or FormFillExtensionState()
        current_state.set(state)
        yield state
        write_model(path_for_state(context), state)
        current_state.set(None)


inspector = FileStateInspector(display_name="Debug: FormFill Agent", file_path_source=path_for_state)
