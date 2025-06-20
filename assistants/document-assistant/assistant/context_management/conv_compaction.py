import asyncio
import io
import json
import logging
import time
import uuid

from assistant_drive import Drive, DriveConfig, IfDriveFileExistsBehavior
from openai.types.chat import (
    ChatCompletionSystemMessageParam,
    ChatCompletionUserMessageParam,
)
from openai_client import create_client
from pydantic import BaseModel
from semantic_workbench_api_model import workbench_model
from semantic_workbench_assistant.assistant_app import (
    ConversationContext,
    storage_directory_for_context,
)

from assistant.config import AssistantConfigModel
from assistant.filesystem import AttachmentsExtension
from assistant.response.utils import get_completion
from assistant.response.utils.openai_utils import convert_oai_messages_to_xml
from assistant.response.utils.workbench_messages import (
    compute_tokens_from_workbench_messages,
    get_workbench_messages,
    workbench_message_to_oai_messages,
)

logger = logging.getLogger(__name__)

_compaction_locks: dict[str, asyncio.Lock] = {}


def _get_compaction_lock_for_context(context: ConversationContext) -> asyncio.Lock:
    """Get or create a conversation-specific lock for compaction operations."""
    if context.id not in _compaction_locks:
        _compaction_locks[context.id] = asyncio.Lock()
    return _compaction_locks[context.id]


COMPACTION_FILE_DIR = "compaction"
COMPACTION_DATA_FILE = "compaction_data.json"

COMPACTION_SYSTEM_PROMPT = """You are summarizing portions of a conversation so they can be easily retrieved. \
You must focus on what the user role wanted, preferred, and any critical information that they shared. \
Always prefer to include information from the user than from any other role. \
Include the content from other roles only as much as necessary to provide the necessary content.
Instead of saying "you said" or "the user said", be specific and use the roles or names to indicate who said what. \
Include the key topics or things that were done.

The summary should be at most four sentences, factual, and free from making anything up or inferences that you are not completely sure about."""


class CompactedChunk(BaseModel):
    chunk_id: uuid.UUID  # This is the unique ID for the compacted chunk
    chunk_name: str
    conv_message_ids: list[uuid.UUID]  # This is the list of workbench message IDs that were compacted into this chunk
    compacted_text: str  # This is the "summary" of the compacted messages
    original_conversation_text: str


class CompactionModel(BaseModel):
    # Mapping from compacted id to the compacted chunk
    compaction_data: dict[uuid.UUID, CompactedChunk]

    # Mapping from workbench message ID to compacted message ID
    def compaction_mapping(self) -> dict[uuid.UUID, uuid.UUID]:
        """
        Returns a mapping from workbench message IDs to compacted chunk IDs.
        """
        mapping = {}
        for chunk in self.compaction_data.values():
            for msg_id in chunk.conv_message_ids:
                mapping[msg_id] = chunk.chunk_id
        return mapping


def _metadata_drive_for_compaction(context: ConversationContext) -> Drive:
    drive_root = storage_directory_for_context(context) / COMPACTION_FILE_DIR
    return Drive(DriveConfig(root=drive_root))


async def get_compaction_data(context: ConversationContext) -> CompactionModel:
    drive = _metadata_drive_for_compaction(context)

    if not drive.file_exists(COMPACTION_DATA_FILE):
        return CompactionModel(compaction_data={})

    try:
        with drive.open_file(COMPACTION_DATA_FILE) as f:
            data = json.load(f)
            return CompactionModel.model_validate(data)
    except Exception as e:
        logger.exception(f"Error reading compaction file: {e}")
        return CompactionModel(compaction_data={})


async def save_compacted_files(context: ConversationContext, compaction_model: CompactionModel) -> None:
    """
    Save the compacted files to the drive.
    """
    drive = _metadata_drive_for_compaction(context)
    data = compaction_model.model_dump(mode="json")
    json_data = json.dumps(data, indent=2).encode("utf-8")

    drive.write(
        content=io.BytesIO(json_data),
        filename=COMPACTION_DATA_FILE,
        if_exists=IfDriveFileExistsBehavior.OVERWRITE,
        content_type="application/json",
    )


async def _remove_orphaned_chunks(
    compaction_model: CompactionModel, existing_message_ids: set[uuid.UUID]
) -> CompactionModel:
    """
    Remove chunks that reference conversation message IDs that no longer exist.
    Returns a new CompactionModel with orphaned chunks removed.
    """
    cleaned_chunks = {}
    orphaned_count = 0
    for chunk_id, chunk in compaction_model.compaction_data.items():
        if any(msg_id in existing_message_ids for msg_id in chunk.conv_message_ids):
            cleaned_chunks[chunk_id] = chunk
        else:
            orphaned_count += 1

    return CompactionModel(compaction_data=cleaned_chunks)


async def task_compact_conversation(
    context: ConversationContext, config: AssistantConfigModel, attachments_extension: AttachmentsExtension
) -> None:
    """
    Analyzes the current conversation messages and what was previously compacted to see if anything new should be compacted.
    Starting from the first message, it should compact in a rolling window.
    The window size is up to compaction_window tokens, with at least one message in the window (regardless of token count).
    The last token_window worth of messages are preserved and not compacted.
    """
    compaction_window = config.orchestration.prompts.token_window

    wb_messages = await get_workbench_messages(context, attachments_extension)
    participants_response = await context.get_participants(include_inactive=True)

    async with _get_compaction_lock_for_context(context):
        compaction_model = await get_compaction_data(context)

        # Remove orphaned chunks first
        existing_message_ids = {msg.id for msg in wb_messages.messages}
        compaction_model = await _remove_orphaned_chunks(compaction_model, existing_message_ids)

        # Build a set of already compacted message IDs for fast lookup
        already_compacted_ids = set()
        for chunk in compaction_model.compaction_data.values():
            already_compacted_ids.update(chunk.conv_message_ids)

        # Find the starting index - after the last message that was compacted
        idx_start = 0
        for i in range(len(wb_messages.messages) - 1, -1, -1):
            if wb_messages.messages[i].id in already_compacted_ids:
                idx_start = i + 1
                break

        # Calculate the end boundary - exclude the last token_window worth of messages
        idx_max_end = len(wb_messages.messages)

        # Find how many messages from the end represent token_window tokens
        tokens_from_end = 0
        messages_to_preserve = 0
        for i in range(len(wb_messages.messages) - 1, -1, -1):
            wb_messages_for_count = wb_messages.model_copy(deep=True)
            wb_messages_for_count.messages = wb_messages_for_count.messages[i:]
            tokens_from_end = await compute_tokens_from_workbench_messages(
                context, wb_messages_for_count, [], participants_response
            )
            messages_to_preserve = len(wb_messages.messages) - i
            if tokens_from_end >= compaction_window:
                break

        # Adjust the max end to preserve these messages
        idx_max_end = len(wb_messages.messages) - messages_to_preserve

        # If all messages are already compacted or we need to preserve everything, nothing to do
        if idx_start >= idx_max_end:
            return

        chunks = list(compaction_model.compaction_data.values())
        current_conv_message_ids = []
        idx_end = idx_start
        while idx_end < idx_max_end:
            current_conv_message_ids.append(wb_messages.messages[idx_end].id)

            wb_messages_for_count = wb_messages.model_copy(deep=True)
            wb_messages_for_count.messages = wb_messages_for_count.messages[idx_start : idx_end + 1]
            current_chunk_tokens = await compute_tokens_from_workbench_messages(
                context, wb_messages_for_count, [], participants_response
            )

            # Check if we've exceeded the window and have more than one message
            if current_chunk_tokens > compaction_window and len(current_conv_message_ids) > 1:
                # Remove last message from the chunk since it caused us to exceed the limit
                current_conv_message_ids.pop()

                # Create chunk WITHOUT the current message
                wb_messages_for_compaction = wb_messages.model_copy(deep=True)
                wb_messages_for_compaction.messages = wb_messages_for_compaction.messages[idx_start:idx_end]

                # Get name for the chunk based on the first and last message timestamps
                chunk_messages = wb_messages_for_compaction.messages
                start_time = chunk_messages[0].timestamp.strftime("%Y%m%d_%H%M%S")
                end_time = chunk_messages[-1].timestamp.strftime("%Y%m%d_%H%M%S")
                chunk_name = f"conversation_{start_time}_{end_time}.txt"

                summary = await _compute_chunk_summary(
                    context, config, wb_messages_for_compaction, participants_response, chunk_name=chunk_name
                )

                full_content = await convert_oai_messages_to_xml(
                    await workbench_message_to_oai_messages(context, wb_messages_for_compaction, participants_response),
                    chunk_name,
                )
                compacted_chunk = CompactedChunk(
                    chunk_id=uuid.uuid4(),
                    chunk_name=chunk_name,
                    conv_message_ids=current_conv_message_ids.copy(),
                    compacted_text=summary,
                    original_conversation_text=full_content,
                )
                chunks.append(compacted_chunk)

                # Reset for next chunk starting at current message
                idx_start = idx_end
                current_conv_message_ids = [wb_messages.messages[idx_end].id]

            idx_end += 1
            # TODO: Remove me
            time.sleep(5)

        compaction_model = CompactionModel(compaction_data={chunk.chunk_id: chunk for chunk in chunks})
        await save_compacted_files(context, compaction_model)


async def _compute_chunk_summary(
    context: ConversationContext,
    config: AssistantConfigModel,
    wb_messages: workbench_model.ConversationMessageList,
    participants_response: workbench_model.ConversationParticipantList,
    chunk_name: str,
) -> str:
    """
    Compute a summary for a chunk of messages.
    """
    oai_messages = await workbench_message_to_oai_messages(context, wb_messages, participants_response)

    conversation_text = await convert_oai_messages_to_xml(
        oai_messages,
        filename=chunk_name,
    )
    summary_messages = [
        ChatCompletionSystemMessageParam(role="system", content=COMPACTION_SYSTEM_PROMPT),
        ChatCompletionUserMessageParam(
            role="user",
            content=f"{conversation_text}\n\nPlease summarize the conversation above according to your instructions.",
        ),
    ]

    async with create_client(config.generative_ai_client_config.service_config) as client:
        summary_response = await get_completion(
            client, config.generative_ai_client_config.request_config, summary_messages, tools=None
        )

    summary = summary_response.choices[0].message.content or ""
    return summary
