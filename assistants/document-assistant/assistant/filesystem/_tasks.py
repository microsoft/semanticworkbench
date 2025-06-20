# Copyright (c) Microsoft. All rights reserved.

import asyncio
import io
import json
import logging

from assistant_drive import Drive, DriveConfig, IfDriveFileExistsBehavior
from openai.types.chat import (
    ChatCompletionSystemMessageParam,
    ChatCompletionUserMessageParam,
)
from openai_client import create_client
from semantic_workbench_assistant.assistant_app import (
    ConversationContext,
    storage_directory_for_context,
)

from assistant.config import AssistantConfigModel
from assistant.filesystem._model import FilesystemFile
from assistant.filesystem._prompts import FILE_SUMMARY_SYSTEM
from assistant.response.utils import get_completion

logger = logging.getLogger(__name__)

_filesystem_metadata_locks: dict[str, asyncio.Lock] = {}


def _get_metadata_lock_for_context(context: ConversationContext) -> asyncio.Lock:
    """Get or create a conversation-specific lock for filesystem metadata operations."""
    if context.id not in _filesystem_metadata_locks:
        _filesystem_metadata_locks[context.id] = asyncio.Lock()
    return _filesystem_metadata_locks[context.id]


def _metadata_drive_for_context(context: ConversationContext) -> Drive:
    drive_root = storage_directory_for_context(context) / "filesystem_metadata"
    return Drive(DriveConfig(root=drive_root))


async def get_filesystem_metadata(ctx: ConversationContext) -> dict[str, FilesystemFile]:
    """
    Get the metadata for all files in the conversation.
    This is mapping from filename to FilesystemFile agnostic of if it is a document or attachment.
    """
    metadata_file_name = "filesystem_metadata.json"
    drive = _metadata_drive_for_context(ctx)
    if not drive.file_exists(metadata_file_name):
        return {}

    try:
        with drive.open_file(metadata_file_name) as f:
            raw_data = json.load(f)
            filesystem_files: dict[str, FilesystemFile] = {}
            for filename, file_data in raw_data.items():
                try:
                    filesystem_files[filename] = FilesystemFile.model_validate(file_data)
                except Exception as e:
                    logger.warning(f"Failed to parse metadata for file {filename}: {e}")

            return filesystem_files
    except Exception as e:
        logger.exception("error reading metadata file", e)
        return {}


async def save_filesystem_metadata(ctx: ConversationContext, metadata: dict[str, FilesystemFile]) -> None:
    drive = _metadata_drive_for_context(ctx)
    data = {filename: file.model_dump() for filename, file in metadata.items()}
    json_data = json.dumps(data, indent=2).encode("utf-8")

    drive.write(
        content=io.BytesIO(json_data),
        filename="filesystem_metadata.json",
        if_exists=IfDriveFileExistsBehavior.OVERWRITE,
        content_type="application/json",
    )


async def task_compute_summary(
    context: ConversationContext,
    config: AssistantConfigModel,
    file_content: str,
    filename: str,
) -> None:
    async with create_client(config.generative_ai_fast_client_config.service_config) as client:
        file_message = f'<file filename="{filename}">\n{file_content}\n</file>\nPlease concisely and accurately summarize the file contents.'
        chat_message_params = [
            ChatCompletionSystemMessageParam(role="system", content=FILE_SUMMARY_SYSTEM),
            ChatCompletionUserMessageParam(role="user", content=file_message),
        ]
        summary_response = await get_completion(
            client, config.generative_ai_fast_client_config.request_config, chat_message_params, tools=None
        )

    summary = summary_response.choices[0].message.content or ""

    async with _get_metadata_lock_for_context(context):
        filesystem_metadata = await get_filesystem_metadata(context)
        current_file_metadata = filesystem_metadata.get(filename, FilesystemFile())
        current_file_metadata.summary = summary
        filesystem_metadata[filename] = current_file_metadata
        await save_filesystem_metadata(context, filesystem_metadata)
