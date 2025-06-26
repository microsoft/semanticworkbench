import asyncio
import contextlib
import io
import logging
from typing import Any, Awaitable, Callable, Sequence

import openai_client
from assistant_drive import IfDriveFileExistsBehavior
from llm_client.model import CompletionMessage, CompletionMessageImageContent, CompletionMessageTextContent
from semantic_workbench_api_model.workbench_model import (
    ConversationEvent,
    File,
    MessageType,
    NewConversationMessage,
)
from semantic_workbench_assistant.assistant_app import (
    AssistantAppProtocol,
    AssistantCapability,
    ConversationContext,
)

from . import _convert as convert
from ._model import Attachment, AttachmentsConfigModel, AttachmentSummary, Summarizer
from ._shared import (
    attachment_drive_for_context,
    attachment_to_original_filename,
    original_to_attachment_filename,
    summary_drive_for_context,
)
from ._summarizer import get_attachment_summary, summarize_attachment_task

logger = logging.getLogger(__name__)


AttachmentProcessingErrorHandler = Callable[[ConversationContext, str, Exception], Awaitable]


async def log_and_send_message_on_error(context: ConversationContext, filename: str, e: Exception) -> None:
    """
    Default error handler for attachment processing, which logs the exception and sends
    a message to the conversation.
    """

    logger.exception("exception occurred processing attachment", exc_info=e)
    await context.send_messages(
        NewConversationMessage(
            content=f"There was an error processing the attachment ({filename}): {e}",
            message_type=MessageType.notice,
            metadata={"attribution": "system"},
        )
    )


attachment_tag = "ATTACHMENT"
filename_tag = "FILENAME"
content_tag = "CONTENT"
error_tag = "ERROR"
image_tag = "IMAGE"


class AttachmentsExtension:
    def __init__(
        self,
        assistant: AssistantAppProtocol,
        error_handler: AttachmentProcessingErrorHandler = log_and_send_message_on_error,
    ) -> None:
        """
        AttachmentsExtension produces chat completion messages for the files in a conversation. These
        messages include the text representations of the files ("attachments"), and their filenames.
        These messages can be included in chat-completion API calls, providing context to the LLM about
        the files in the conversation.

        Args:
            assistant: The assistant app to bind to.
            error_handler: The error handler to be notified when errors occur while extracting attachments
            from files.

        Example:
            ```python
            from assistant_extensions.attachments import AttachmentsExtension

            assistant = AssistantApp(...)

            attachments_extension = AttachmentsExtension(assistant)


            @assistant.events.conversation.message.chat.on_created
            async def on_message_created(
                context: ConversationContext, event: ConversationEvent, message: ConversationMessage
            ) -> None:
                ...
                config = ...
                completion_messages = await attachments_extension.get_completion_messages_for_attachments(
                    context,
                    config,
                )
            ```
        """

        self._error_handler = error_handler

        # add the 'supports_conversation_files' capability to the assistant, to indicate that this
        # assistant supports files in the conversation
        assistant.add_capability(AssistantCapability.supports_conversation_files)

        # listen for file events for to pro-actively update and delete attachments

        @assistant.events.conversation.file.on_deleted_including_mine
        async def on_file_deleted(context: ConversationContext, event: ConversationEvent, file: File) -> None:
            """
            Delete an attachment when a file is deleted in the conversation.
            """

            # delete the attachment for the file
            await _delete_attachment_for_file(context, file)

    async def get_completion_messages_for_attachments(
        self,
        context: ConversationContext,
        config: AttachmentsConfigModel,
        include_filenames: list[str] | None = None,
        exclude_filenames: list[str] = [],
        summarizer: Summarizer | None = None,
    ) -> Sequence[CompletionMessage]:
        """
        Generate user messages for each attachment that includes the filename and content.

        In the case of images, the content will be a data URI, other file types will be included as text.

        Args:
            context: The conversation context.
            config: The configuration for the attachment agent.
            include_filenames: The filenames of the attachments to include.
            exclude_filenames: The filenames of the attachments to exclude. If provided, this will take precedence over include_filenames.

        Returns:
            A list of messages for the chat completion.
        """

        # get attachments, filtered by include_filenames and exclude_filenames
        attachments = await get_attachments(
            context,
            error_handler=self._error_handler,
            include_filenames=include_filenames,
            exclude_filenames=exclude_filenames,
        )

        if not attachments:
            return []

        messages: list[CompletionMessage] = [_create_message(config.preferred_message_role, config.context_description)]

        # process each attachment
        for attachment in attachments:
            messages.append(_create_message_for_attachment(config.preferred_message_role, attachment))

        return messages

    async def get_attachment_filenames(
        self,
        context: ConversationContext,
        include_filenames: list[str] | None = None,
        exclude_filenames: list[str] = [],
    ) -> list[str]:
        files_response = await context.list_files()

        # for all files, get the attachment
        for file in files_response.files:
            if include_filenames is not None and file.filename not in include_filenames:
                continue
            if file.filename in exclude_filenames:
                continue

        # delete cached attachments that are no longer in the conversation
        filenames = list({file.filename for file in files_response.files})

        return filenames


def _create_message_for_attachment(preferred_message_role: str, attachment: Attachment) -> CompletionMessage:
    # if the content is a data URI, include it as an image type within the message content
    if attachment.content.startswith("data:image/"):
        return CompletionMessage(
            role="user",
            content=[
                CompletionMessageTextContent(
                    type="text",
                    text=f"<{attachment_tag}><{filename_tag}>{attachment.filename}</{filename_tag}><{image_tag}>",
                ),
                CompletionMessageImageContent(
                    type="image",
                    media_type="image/png",
                    data=attachment.content,
                ),
                CompletionMessageTextContent(
                    type="text",
                    text=f"</{image_tag}></{attachment_tag}>",
                ),
            ],
        )

    error_element = f"<{error_tag}>{attachment.error}</{error_tag}>" if attachment.error else ""
    content = f"<{attachment_tag}><{filename_tag}>{attachment.filename}</{filename_tag}>{error_element}<{content_tag}>{attachment.content}</{content_tag}></{attachment_tag}>"
    return _create_message(preferred_message_role, content)


def _create_message(preferred_message_role: str, content: str) -> CompletionMessage:
    match preferred_message_role:
        case "system":
            return CompletionMessage(
                role="system",
                content=content,
            )
        case "user":
            return CompletionMessage(
                role="user",
                content=content,
            )
        case _:
            raise ValueError(f"unsupported preferred_message_role: {preferred_message_role}")


async def default_error_handler(context: ConversationContext, filename: str, e: Exception) -> None:
    logger.exception("error reading file %s", filename, exc_info=e)


async def get_attachments(
    context: ConversationContext,
    include_filenames: list[str] | None,
    exclude_filenames: list[str],
    error_handler: AttachmentProcessingErrorHandler = default_error_handler,
    summarizer: Summarizer | None = None,
) -> Sequence[Attachment]:
    """
    Gets all attachments for the current state of the conversation, updating the cache as needed.
    """

    # get all files in the conversation
    files_response = await context.list_files()

    attachments = []
    # for all files, get the attachment
    for file in files_response.files:
        if include_filenames is not None and file.filename not in include_filenames:
            continue
        if file.filename in exclude_filenames:
            continue

        attachment = await _get_attachment_for_file(context, file, {}, error_handler, summarizer=summarizer)
        attachments.append(attachment)

    # delete cached attachments that are no longer in the conversation
    filenames = {file.filename for file in files_response.files}
    await _delete_attachments_not_in(context, filenames)

    return attachments


async def _delete_attachments_not_in(context: ConversationContext, filenames: set[str]) -> None:
    """Deletes cached attachments that are not in the filenames argument."""
    drive = attachment_drive_for_context(context)
    summary_drive = summary_drive_for_context(context)
    for attachment_filename in drive.list():
        if attachment_filename == "summaries":
            continue

        original_file_name = attachment_to_original_filename(attachment_filename)
        if original_file_name in filenames:
            continue

        with contextlib.suppress(FileNotFoundError):
            drive.delete(attachment_filename)

        with contextlib.suppress(FileNotFoundError):
            summary_drive.delete(attachment_filename)

        await _delete_lock_for_context_file(context, original_file_name)


_file_locks_lock = asyncio.Lock()
_file_locks: dict[str, asyncio.Lock] = {}


async def _delete_lock_for_context_file(context: ConversationContext, filename: str) -> None:
    async with _file_locks_lock:
        key = f"{context.assistant.id}/{context.id}/{filename}"
        if key not in _file_locks:
            return

        del _file_locks[key]


async def _lock_for_context_file(context: ConversationContext, filename: str) -> asyncio.Lock:
    """
    Get a lock for the given file in the given context.
    """
    async with _file_locks_lock:
        key = f"{context.assistant.id}/{context.id}/{filename}"
        if key not in _file_locks:
            _file_locks[key] = asyncio.Lock()

        return _file_locks[key]


async def _get_attachment_for_file(
    context: ConversationContext,
    file: File,
    metadata: dict[str, Any],
    error_handler: AttachmentProcessingErrorHandler,
    summarizer: Summarizer | None = None,
) -> Attachment:
    """
    Get the attachment for the file. If the attachment is not cached, or the file is
    newer than the cached attachment, the text content of the file will be extracted
    and the cache will be updated.
    """

    # ensure that only one async task is updating the attachment for the file
    file_lock = await _lock_for_context_file(context, file.filename)
    async with file_lock:
        attachment = await _get_or_update_attachment(
            context=context,
            file=file,
            metadata=metadata,
            error_handler=error_handler,
        )

        summary = AttachmentSummary(summary="")
        if summarizer:
            summary = await _get_or_update_attachment_summary(
                context=context,
                attachment=attachment,
                summarizer=summarizer,
            )

    return attachment.model_copy(update={"summary": summary})


async def _get_or_update_attachment(
    context: ConversationContext, file: File, metadata: dict[str, Any], error_handler: AttachmentProcessingErrorHandler
) -> Attachment:
    drive = attachment_drive_for_context(context)

    with contextlib.suppress(FileNotFoundError):
        attachment = drive.read_model(Attachment, original_to_attachment_filename(file.filename))

        if attachment.updated_datetime.timestamp() >= file.updated_datetime.timestamp():
            # if the attachment is up-to-date, return it
            return attachment

    content = ""
    error = ""
    # process the file to create an attachment
    async with context.set_status(f"updating attachment {file.filename}..."):
        try:
            # read the content of the file
            file_bytes = await _read_conversation_file(context, file)
            # convert the content of the file to a string
            content = await convert.bytes_to_str(file_bytes, filename=file.filename)
        except Exception as e:
            await error_handler(context, file.filename, e)
            error = f"error processing file: {e}"

    attachment = Attachment(
        filename=file.filename,
        content=content,
        metadata=metadata,
        updated_datetime=file.updated_datetime,
        error=error,
    )
    drive.write_model(
        attachment, original_to_attachment_filename(file.filename), if_exists=IfDriveFileExistsBehavior.OVERWRITE
    )

    completion_message = _create_message_for_attachment(preferred_message_role="system", attachment=attachment)
    openai_completion_messages = openai_client.messages.convert_from_completion_messages([completion_message])
    token_count = openai_client.num_tokens_from_message(openai_completion_messages[0], model="gpt-4o")

    # update the conversation token count based on the token count of the latest version of this file
    prior_token_count = file.metadata.get("token_count", 0)
    conversation = await context.get_conversation()
    token_counts = conversation.metadata.get("token_counts", {})
    if token_counts:
        total = token_counts.get("total", 0)
        total += token_count - prior_token_count
        await context.update_conversation({
            "token_counts": {
                **token_counts,
                "total": total,
            },
        })

    await context.update_file(
        file.filename,
        metadata={
            "token_count": token_count,
        },
    )

    return attachment


async def _get_or_update_attachment_summary(
    context: ConversationContext, attachment: Attachment, summarizer: Summarizer
) -> AttachmentSummary:
    attachment_summary = await get_attachment_summary(
        context=context,
        filename=attachment.filename,
    )
    if attachment_summary.updated_datetime.timestamp() < attachment.updated_datetime.timestamp():
        # if the summary is not up-to-date, schedule a task to update it
        asyncio.create_task(
            summarize_attachment_task(
                context=context,
                summarizer=summarizer,
                attachment=attachment,
            )
        )

    return attachment_summary


async def _delete_attachment_for_file(context: ConversationContext, file: File) -> None:
    drive = attachment_drive_for_context(context)

    with contextlib.suppress(FileNotFoundError):
        drive.delete(file.filename)

    summary_drive = summary_drive_for_context(context)
    with contextlib.suppress(FileNotFoundError):
        summary_drive.delete(file.filename)

    await _delete_lock_for_context_file(context, file.filename)

    # update the conversation token count based on the token count of the latest version of this file
    file_token_count = file.metadata.get("token_count", 0)
    if not file_token_count:
        return

    conversation = await context.get_conversation()
    token_counts = conversation.metadata.get("token_counts", {})
    if not token_counts:
        return

    total = token_counts.get("total", 0)
    if not total:
        return

    total -= file_token_count

    await context.update_conversation({
        "token_counts": {
            **token_counts,
            "total": total,
        },
    })


async def _read_conversation_file(context: ConversationContext, file: File) -> bytes:
    """
    Read the content of the file with the given filename.
    """
    buffer = io.BytesIO()

    async with context.read_file(file.filename) as reader:
        async for chunk in reader:
            buffer.write(chunk)

    buffer.seek(0)
    return buffer.read()
