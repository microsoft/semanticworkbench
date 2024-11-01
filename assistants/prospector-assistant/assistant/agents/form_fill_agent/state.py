from contextlib import asynccontextmanager
from contextvars import ContextVar
from enum import StrEnum
from pathlib import Path
from typing import AsyncIterator

from pydantic import BaseModel
from semantic_workbench_api_model.workbench_model import AssistantStateEvent
from semantic_workbench_assistant.assistant_app.context import ConversationContext, storage_directory_for_context
from semantic_workbench_assistant.storage import read_model, write_model

from .steps import extract_form_fields


class FormFillAgentMode(StrEnum):
    acquire_form_step = "acquire_form"
    extract_form_fields_step = "extract_form_fields"
    fill_form_step = "fill_form"
    generate_filled_form_step = "generate_filled_form"

    end_conversation = "end_conversation"


class FormFillAgentState(BaseModel):
    mode: FormFillAgentMode = FormFillAgentMode.acquire_form_step
    most_recent_attachment_timestamp: float = 0
    form_filename: str = ""
    extracted_form_fields: list[extract_form_fields.FormField] = []
    fill_form_gc_artifact: dict | None = None

    mode_debug_log: dict[FormFillAgentMode, list[dict]] = {}


def path_for_state(context: ConversationContext) -> Path:
    return storage_directory_for_context(context) / "state.json"


current_state = ContextVar[FormFillAgentState | None]("current_state", default=None)


@asynccontextmanager
async def agent_state(context: ConversationContext) -> AsyncIterator[FormFillAgentState]:
    state = current_state.get()
    if state is not None:
        yield state
        return

    state = read_model(path_for_state(context), FormFillAgentState) or FormFillAgentState()
    current_state.set(state)
    yield state
    write_model(path_for_state(context), state)
    await context.send_conversation_state_event(
        AssistantStateEvent(state_id="form_fill_agent", event="updated", state=None)
    )
    current_state.set(None)
