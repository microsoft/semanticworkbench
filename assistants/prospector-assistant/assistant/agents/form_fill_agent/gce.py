import asyncio
import contextlib
import json
from collections import defaultdict
from contextlib import asynccontextmanager
from pathlib import Path
from typing import Annotated, AsyncIterator, Awaitable, Callable, Sequence

from guided_conversation.guided_conversation_agent import GuidedConversation
from guided_conversation.utils.resources import ResourceConstraint, ResourceConstraintMode, ResourceConstraintUnit
from openai import AsyncOpenAI
from openai.types.chat import ChatCompletionMessageParam
from pydantic import BaseModel, ConfigDict, Field
from semantic_kernel import Kernel
from semantic_kernel.connectors.ai.open_ai import OpenAIChatCompletion
from semantic_workbench_assistant.assistant_app.context import ConversationContext, storage_directory_for_context

from . import state


class ResourceConstraintDefinition(BaseModel):
    model_config = ConfigDict(
        json_schema_extra={
            "required": ["quantity", "unit", "mode"],
        },
    )

    quantity: Annotated[int, Field(title="Quantity", description="The quantity of the resource constraint.")]
    unit: Annotated[ResourceConstraintUnit, Field(title="Unit", description="Unit of the resource constraint.")]
    mode: Annotated[ResourceConstraintMode, Field(title="Mode", description="Mode of the resource constraint.")]

    def to_resource_constraint(self) -> ResourceConstraint:
        return ResourceConstraint(
            quantity=self.quantity,
            unit=self.unit,
            mode=self.mode,
        )


class GuidedConversationDefinition(BaseModel):
    model_config = ConfigDict(json_schema_extra={"required": ["rules", "resource_constraint"]})

    rules: Annotated[
        list[str],
        Field(title="Rules", description="The do's and don'ts that the agent should follow during the conversation."),
    ]

    conversation_flow: Annotated[
        str,
        Field(
            title="Conversation flow",
            description="(optional) Defines the steps of the conversation in natural language.",
        ),
    ]

    context: Annotated[
        str,
        Field(
            title="Context",
            description="(optional) Any additional information or the circumstances the agent is in that it should be aware of. It can also include the high level goal of the conversation if needed.",
        ),
    ]

    resource_constraint: Annotated[
        ResourceConstraintDefinition,
        Field(title="Resource constraint", description="Defines how the guided-conversation should be constrained."),
    ]


guided_conversation_locks: dict[Path, asyncio.Lock] = defaultdict(asyncio.Lock)


@asynccontextmanager
async def guided_conversation_with_state(
    openai_client: AsyncOpenAI,
    openai_model: str,
    definition: GuidedConversationDefinition,
    artifact_type: type[BaseModel],
    state_file_path: Path,
) -> AsyncIterator[GuidedConversation]:
    # ensure that only one guided conversation is executed at a time for any given state file
    # ie. require them to run sequentially
    async with guided_conversation_locks[state_file_path]:
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

            guided_conversation.resource.resource_constraint = definition.resource_constraint.to_resource_constraint()

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
    latest_user_message: str | None,
    get_attachment_messages: Callable[[Sequence[str]], Awaitable[Sequence[ChatCompletionMessageParam]]],
) -> str:
    files = await context.get_files()

    new_filenames = set()

    async with state.agent_state(context) as agent_state:
        max_timestamp = agent_state.most_recent_attachment_timestamp
        for file in files.files:
            if file.updated_datetime.timestamp() <= agent_state.most_recent_attachment_timestamp:
                continue

            max_timestamp = max(file.updated_datetime.timestamp(), max_timestamp)
            new_filenames.add(file.filename)

        agent_state.most_recent_attachment_timestamp = max_timestamp

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


def path_for_guided_conversation_state(context: ConversationContext, mode: state.FormFillAgentMode) -> Path:
    dir = storage_directory_for_context(context) / str(mode)
    dir.mkdir(parents=True, exist_ok=True)
    return dir / "guided_conversation_state.json"
