import asyncio
import contextlib
import json
from collections import defaultdict
from contextlib import asynccontextmanager
from pathlib import Path
from typing import AsyncIterator, Awaitable, Callable, Sequence

from assistant.agents.form_fill_agent.inspector import state_change_event_after
from guided_conversation.guided_conversation_agent import GuidedConversation
from openai import AsyncOpenAI
from openai.types.chat import ChatCompletionMessageParam
from pydantic import BaseModel
from semantic_kernel import Kernel
from semantic_kernel.connectors.ai.open_ai import OpenAIChatCompletion
from semantic_workbench_assistant.assistant_app.context import ConversationContext, storage_directory_for_context

from .. import gce_config, state

guided_conversation_locks: dict[Path, asyncio.Lock] = defaultdict(asyncio.Lock)


@asynccontextmanager
async def guided_conversation_with_state(
    openai_client: AsyncOpenAI,
    openai_model: str,
    definition: gce_config.GuidedConversationDefinition,
    artifact_type: type[BaseModel],
    state_file_path: Path,
    context: ConversationContext,
    state_id: str,
) -> AsyncIterator[GuidedConversation]:
    # ensure that only one guided conversation is executed at a time for any given state file
    # ie. require them to run sequentially
    async with guided_conversation_locks[state_file_path], state_change_event_after(context, state_id):
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


def path_for_guided_conversation_state(context: ConversationContext, dir: str) -> Path:
    dir_path = storage_directory_for_context(context) / dir
    dir_path.mkdir(parents=True, exist_ok=True)
    return dir_path / "guided_conversation_state.json"
