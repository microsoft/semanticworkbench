"""
Utility functions for working with guided conversations.
"""

import asyncio
import contextlib
import json
from collections import defaultdict
from contextlib import asynccontextmanager
from pathlib import Path
from typing import AsyncIterator

from guided_conversation.guided_conversation_agent import GuidedConversation
from openai import AsyncOpenAI
from pydantic import BaseModel
from semantic_kernel import Kernel
from semantic_kernel.connectors.ai.open_ai import OpenAIChatCompletion
from semantic_workbench_assistant.assistant_app.context import ConversationContext, storage_directory_for_context

from .types import GuidedConversationDefinition

_state_locks: dict[Path, asyncio.Lock] = defaultdict(asyncio.Lock)


@asynccontextmanager
async def engine(
    openai_client: AsyncOpenAI,
    openai_model: str,
    definition: GuidedConversationDefinition,
    artifact_type: type[BaseModel],
    state_file_path: Path,
    context: ConversationContext,
    state_id: str,
) -> AsyncIterator[GuidedConversation]:
    """
    Context manager that provides a guided conversation engine with state, reading it from disk, and saving back
    to disk after the context manager block is executed.

    NOTE: This context manager uses a lock to ensure that only one guided conversation is executed at a time for any
    given state file.
    """

    async with _state_locks[state_file_path], context.state_updated_event_after(state_id):
        kernel, service_id = _build_kernel_with_service(openai_client, openai_model)

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
                artifact=artifact_type,
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
                artifact=artifact_type,
                rules=definition.rules,
                conversation_flow=definition.conversation_flow,
                context=definition.context,
                resource_constraint=definition.resource_constraint.to_resource_constraint(),
            )

        yield guided_conversation

        state = guided_conversation.to_json()
        # re-order the keys to make the json more readable in the state file
        state = {
            "artifact": state.pop("artifact"),
            "agenda": state.pop("agenda"),
            "resource": state.pop("resource"),
            "chat_history": state.pop("chat_history"),
            **state,
        }
        state_file_path.write_text(json.dumps(state), encoding="utf-8")


def _build_kernel_with_service(openai_client: AsyncOpenAI, openai_model: str) -> tuple[Kernel, str]:
    kernel = Kernel()
    service_id = "gc_main"
    chat_service = OpenAIChatCompletion(
        service_id=service_id,
        async_client=openai_client,
        ai_model_id=openai_model,
    )
    kernel.add_service(chat_service)
    return kernel, service_id


def path_for_state(context: ConversationContext, dir: str) -> Path:
    dir_path = storage_directory_for_context(context) / dir
    dir_path.mkdir(parents=True, exist_ok=True)
    return dir_path / "guided_conversation_state.json"
