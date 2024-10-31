import contextlib
import json
import logging
from contextlib import asynccontextmanager, contextmanager
from contextvars import ContextVar
from enum import StrEnum
from pathlib import Path
from typing import AsyncIterator, Awaitable, Callable, Iterator, Sequence

from assistant.agents.form_fill_agent import fill_form
from guided_conversation.guided_conversation_agent import GuidedConversation
from openai import AsyncOpenAI
from openai.types.chat import ChatCompletionMessageParam
from pydantic import BaseModel
from semantic_kernel import Kernel
from semantic_kernel.connectors.ai.open_ai import OpenAIChatCompletion
from semantic_workbench_api_model.workbench_model import AssistantStateEvent, MessageType, NewConversationMessage
from semantic_workbench_assistant.assistant_app.context import ConversationContext, storage_directory_for_context
from semantic_workbench_assistant.assistant_app.protocol import (
    AssistantConversationInspectorStateDataModel,
    ReadOnlyAssistantConversationInspectorStateProvider,
)
from semantic_workbench_assistant.storage import read_model, write_model

from . import acquire_form, extract_form_fields
from .config import FormFillAgentConfig
from .definition import GuidedConversationDefinition
from .llm_config import LLMConfig

logger = logging.getLogger(__name__)


class FormFillAgentMode(StrEnum):
    acquire_form = "acquire_form"
    fill_form = "fill_form"
    generate_filled_form = "generate_filled_form"

    end_conversation = "end_conversation"


class FormFillAgentState(BaseModel):
    mode: FormFillAgentMode = FormFillAgentMode.acquire_form
    most_recent_attachment_timestamp: float = 0
    acquire_form_gc_artifact: dict | None = None
    extracted_form_fields: extract_form_fields.FormFields | None = None
    form_filename: str = ""
    fill_form_gc_artifact: dict | None = None


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


def path_for_guided_conversation_state(context: ConversationContext, mode: FormFillAgentMode) -> Path:
    dir = storage_directory_for_context(context) / str(mode)
    dir.mkdir(parents=True, exist_ok=True)
    return dir / "guided_conversation_state.json"


class FileStateInspector(ReadOnlyAssistantConversationInspectorStateProvider):
    def __init__(
        self, display_name: str, file_path_source: Callable[[ConversationContext], Path], description: str = ""
    ) -> None:
        self._display_name = display_name
        self._file_path_source = file_path_source
        self._description = description

    @property
    def display_name(self) -> str:
        return self._display_name

    @property
    def description(self) -> str:
        return self._description

    async def get(self, context: ConversationContext) -> AssistantConversationInspectorStateDataModel:
        def read_state(path: Path) -> dict:
            with contextlib.suppress(FileNotFoundError):
                return json.loads(path.read_text(encoding="utf-8"))
            return {}

        return AssistantConversationInspectorStateDataModel(
            data=read_state(self._file_path_source(context)),
        )


FormFillAgentStateInspector = FileStateInspector(display_name="Form Fill Agent State", file_path_source=path_for_state)
AcquireFormGuidedConversationStateInspector = FileStateInspector(
    display_name="Acquire Form Guided Conversation State",
    file_path_source=lambda context: path_for_guided_conversation_state(context, FormFillAgentMode.acquire_form),
)
FillFormGuidedConversationStateInspector = FileStateInspector(
    display_name="Fill Form Guided Conversation State",
    file_path_source=lambda context: path_for_guided_conversation_state(context, FormFillAgentMode.fill_form),
)


@contextmanager
def guided_conversation_with_state(
    openai_client: AsyncOpenAI,
    openai_model: str,
    definition: GuidedConversationDefinition,
    artifact_type: type[BaseModel],
    state_file_path: Path,
) -> Iterator[GuidedConversation]:
    kernel, service_id = build_kernel_with_service(openai_client, openai_model)

    state: dict | None = None
    with contextlib.suppress(FileNotFoundError):
        state = json.loads(state_file_path.read_text(encoding="utf-8"))

    if state:
        guided_conversation = GuidedConversation.from_json(
            json_data=state,
            # dependencies
            kernel=kernel,
            service_id=service_id,
            # context
            artifact=artifact_type.model_construct(),
            rules=definition.rules,
            conversation_flow=definition.conversation_flow,
            context=definition.context,
            resource_constraint=definition.resource_constraint.to_resource_constraint(),
        )

    else:
        guided_conversation = GuidedConversation(
            # dependencies
            kernel=kernel,
            service_id=service_id,
            # context
            artifact=artifact_type.model_construct(),
            rules=definition.rules,
            conversation_flow=definition.conversation_flow,
            context=definition.context,
            resource_constraint=definition.resource_constraint.to_resource_constraint(),
        )

    yield guided_conversation

    state = guided_conversation.to_json()
    state_file_path.write_text(json.dumps(state), encoding="utf-8")


def build_kernel_with_service(openai_client: AsyncOpenAI, openai_model: str) -> tuple[Kernel, str]:
    kernel = Kernel()
    service_id = "gc_main"
    chat_service = OpenAIChatCompletion(
        service_id=service_id,
        async_client=openai_client,
        ai_model_id=openai_model,
    )
    kernel.add_service(chat_service)
    return kernel, service_id


async def message_with_recent_attachments(
    context: ConversationContext,
    state: FormFillAgentState,
    latest_user_message: str | None,
    get_attachment_messages: Callable[[Sequence[str]], Awaitable[Sequence[ChatCompletionMessageParam]]],
) -> str:
    files = await context.get_files()

    new_filenames = set()
    max_timestamp = state.most_recent_attachment_timestamp
    for file in files.files:
        if file.updated_datetime.timestamp() <= state.most_recent_attachment_timestamp:
            continue

        max_timestamp = max(file.updated_datetime.timestamp(), max_timestamp)
        new_filenames.add(file.filename)

    state.most_recent_attachment_timestamp = max_timestamp

    attachment_messages = await get_attachment_messages(list(new_filenames))

    return "\n\n".join(
        (
            latest_user_message or "",
            *(
                str(attachment.get("content"))
                for attachment in attachment_messages
                if "<ATTACHMENT>" in str(attachment.get("content", ""))
            ),
        ),
    )


async def attachment_for_filename(
    filename: str, get_attachment_messages: Callable[[Sequence[str]], Awaitable[Sequence[ChatCompletionMessageParam]]]
) -> str:
    attachment_messages = await get_attachment_messages([filename])
    return "\n\n".join(
        (
            str(attachment.get("content"))
            for attachment in attachment_messages
            if "<ATTACHMENT>" in str(attachment.get("content", ""))
        )
    )


class FormFillAgent:
    @staticmethod
    async def step(
        context: ConversationContext,
        llm_config: LLMConfig,
        config: FormFillAgentConfig,
        latest_user_message: str | None,
        get_attachment_messages: Callable[[Sequence[str]], Awaitable[Sequence[ChatCompletionMessageParam]]],
    ) -> None:
        async with agent_state(context) as state:
            match state.mode:
                case FormFillAgentMode.acquire_form:
                    message_with_attachments = await message_with_recent_attachments(
                        context, state, latest_user_message, get_attachment_messages
                    )

                    with guided_conversation_with_state(
                        definition=config.acquire_form_config,
                        artifact_type=acquire_form.FormArtifact,
                        state_file_path=path_for_guided_conversation_state(context, state.mode),
                        openai_client=llm_config.openai_client,
                        openai_model=llm_config.openai_model,
                    ) as guided_conversation:
                        result = await guided_conversation.step_conversation(message_with_attachments)
                        logger.info("guided-conversation result: %s", result)

                        state.acquire_form_gc_artifact = guided_conversation.artifact.artifact.model_dump(mode="json")
                        logger.info("guided-conversation artifact: %s", guided_conversation.artifact)

                    if result.ai_message:
                        await context.send_messages(NewConversationMessage(content=result.ai_message))

                    state.form_filename = state.acquire_form_gc_artifact.get("filename", "")
                    if state.form_filename and state.form_filename != "Unanswered":
                        file_content = await attachment_for_filename(state.form_filename, get_attachment_messages)
                        async with context.set_status_for_block("inspecting form ..."):
                            try:
                                state.extracted_form_fields, metadata = await extract_form_fields.extract(
                                    llm_config=llm_config,
                                    config=config.extract_form_fields_config,
                                    form_content=file_content,
                                )

                                await context.send_messages(
                                    NewConversationMessage(
                                        content=f"Form fields extracted: ```json\n{state.extracted_form_fields.model_dump_json()}\n```",
                                        message_type=MessageType.notice,
                                        metadata={
                                            "debug": metadata,
                                        },
                                    )
                                )

                            except (
                                extract_form_fields.NoResponseChoicesError,
                                extract_form_fields.NoParsedMessageError,
                            ):
                                logger.exception("failed to extract form fields")

                        if state.extracted_form_fields and state.extracted_form_fields.error_message:
                            await context.send_messages(
                                NewConversationMessage(
                                    content=state.extracted_form_fields.error_message,
                                    metadata={
                                        "debug": metadata,
                                    },
                                )
                            )

                        if state.extracted_form_fields and not state.extracted_form_fields.error_message:
                            logger.info("changing mode; from: %s, to: %s", state.mode, FormFillAgentMode.fill_form)
                            state.mode = FormFillAgentMode.fill_form

                    if result.is_conversation_over:
                        logger.info("changing mode; from: %s, to: %s", state.mode, FormFillAgentMode.end_conversation)
                        state.mode = FormFillAgentMode.end_conversation

                case FormFillAgentMode.fill_form:
                    message_with_attachments = await message_with_recent_attachments(
                        context, state, latest_user_message, get_attachment_messages
                    )

                    if state.extracted_form_fields is None:
                        raise ValueError("extracted_form_fields is None")

                    artifact_type = fill_form.form_fields_to_artifact(state.extracted_form_fields)

                    with guided_conversation_with_state(
                        definition=config.fill_form_config,
                        artifact_type=artifact_type,
                        state_file_path=path_for_guided_conversation_state(context, state.mode),
                        openai_client=llm_config.openai_client,
                        openai_model=llm_config.openai_model,
                    ) as guided_conversation:
                        result = await guided_conversation.step_conversation(message_with_attachments)
                        logger.info("guided-conversation result: %s", result)

                        state.fill_form_gc_artifact = guided_conversation.artifact.artifact.model_dump(mode="json")
                        logger.info("guided-conversation artifact: %s", guided_conversation.artifact)

                    if result.ai_message:
                        await context.send_messages(NewConversationMessage(content=result.ai_message))

                    if result.is_conversation_over:
                        logger.info("changing mode; from: %s, to: %s", state.mode, FormFillAgentMode.end_conversation)
                        state.mode = FormFillAgentMode.end_conversation

                case FormFillAgentMode.generate_filled_form:
                    pass

                case FormFillAgentMode.end_conversation:
                    await context.send_messages(NewConversationMessage(content="Conversation has ended."))
