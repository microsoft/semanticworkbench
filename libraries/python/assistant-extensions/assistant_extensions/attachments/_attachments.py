import contextlib
import datetime
import io
import logging
from typing import Any, Awaitable, Callable, Sequence

from assistant_drive import Drive, DriveConfig
from openai.types import chat
from semantic_workbench_api_model.workbench_model import (
    ConversationEvent,
    File,
    MessageType,
    NewConversationMessage,
)
from semantic_workbench_assistant.assistant_app import (
    AssistantApp,
    ConversationContext,
    storage_directory_for_context,
)

from . import _convert as convert
from ._model import Attachment, AttachmentsConfigModel

logger = logging.getLogger(__name__)


AttachmentProcessingErrorHandler = Callable[[ConversationContext, Exception], Awaitable]


async def log_and_send_message_on_error(context: ConversationContext, e: Exception) -> None:
    """
    Default error handler for attachment processing, which logs the exception and sends
    a message to the conversation.
    """

    logger.exception("exception occurred processing attachment")
    await context.send_messages(
        NewConversationMessage(
            content=f"There was an error processing the attachment: {e}",
            message_type=MessageType.chat,
            metadata={"attribution": "system"},
        )
    )


attachment_tag = "ATTACHMENT"
filename_tag = "FILENAME"
content_tag = "CONTENT"
image_tag = "IMAGE"


class AttachmentsExtension:
    def __init__(
        self,
        assistant: AssistantApp,
        error_handler: AttachmentProcessingErrorHandler = log_and_send_message_on_error,
    ) -> None:
        """
        AttachmentsExtension produces chat completion messages for the files in a conversation. These
        messages include the text represenations of the files ("attachments"), and their filenames.
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

        # listen for file events for to pro-actively update and delete attachments

        @assistant.events.conversation.file.on_created
        @assistant.events.conversation.file.on_updated
        async def on_file_created_or_updated(
            context: ConversationContext, event: ConversationEvent, file: File
        ) -> None:
            """
            Cache an attachment when a file is created or updated in the conversation.
            """

            await _get_attachment_for_file(context, file, {}, error_handler=self._error_handler)

        @assistant.events.conversation.file.on_deleted
        async def on_file_deleted(context: ConversationContext, event: ConversationEvent, file: File) -> None:
            """
            Delete an attachment when a file is deleted in the conversation.
            """

            # delete the attachment for the file
            _delete_attachment_for_file(context, file)

    async def get_completion_messages_for_attachments(
        self,
        context: ConversationContext,
        config: AttachmentsConfigModel,
        include_filenames: list[str] = [],
        exclude_filenames: list[str] = [],
    ) -> Sequence[chat.ChatCompletionSystemMessageParam | chat.ChatCompletionUserMessageParam]:
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

        if not config.include_in_response_generation:
            return []

        # get attachments, filtered by include_filenames and exclude_filenames
        attachments = await _get_attachments(
            context,
            error_handler=self._error_handler,
            include_filenames=include_filenames,
            exclude_filenames=exclude_filenames,
        )

        if attachments:
            return []

        messages: list[chat.ChatCompletionSystemMessageParam | chat.ChatCompletionUserMessageParam] = [
            {
                "role": "system",
                "content": config.context_description,
            }
        ]

        # process each attachment
        for attachment in attachments:
            content = f"<{attachment_tag}><{filename_tag}>{attachment.filename}</{filename_tag}><{content_tag}>{attachment.content}</{content_tag}></{attachment_tag}>"

            # if the content is a data URI, include it as an image type within the message content
            if attachment.content.startswith("data:image/"):
                content = [
                    {
                        "type": "text",
                        "text": f"<{attachment_tag}><{filename_tag}>{attachment.filename}</{filename_tag}><{image_tag}>",
                    },
                    {
                        "type": "image_url",
                        "image_url": {
                            "url": attachment.content,
                        },
                    },
                    {
                        "type": "text",
                        "text": f"</{image_tag}></{attachment_tag}>",
                    },
                ]

            messages.append({
                "role": "user",
                "content": content,
            })

        return messages


async def _get_attachments(
    context: ConversationContext,
    error_handler: AttachmentProcessingErrorHandler,
    include_filenames: list[str] = [],
    exclude_filenames: list[str] = [],
) -> Sequence[Attachment]:
    """
    Gets all attachments for the current state of the conversation, updating the cache as needed.
    """

    # get all files in the conversation
    files_response = await context.get_files()

    attachments = []
    # for all files, get the attachment
    for file in files_response.files:
        if include_filenames and file.filename not in include_filenames:
            continue
        if file.filename in exclude_filenames:
            continue

        attachment = await _get_attachment_for_file(context, file, {}, error_handler)
        attachments.append(attachment)

    # delete cached attachments that are no longer in the conversation
    filenames = {file.filename for file in files_response.files}
    _delete_attachments_not_in(context, filenames)

    return attachments


def _delete_attachments_not_in(context: ConversationContext, filenames: set[str]) -> None:
    """Deletes cached attachments that are not in the filenames argument."""
    drive = _attachment_drive_for_context(context)
    for filename in drive.list():
        if filename in filenames:
            continue

        with contextlib.suppress(FileNotFoundError):
            drive.delete(filename)


async def _get_attachment_for_file(
    context: ConversationContext, file: File, metadata: dict[str, Any], error_handler: AttachmentProcessingErrorHandler
) -> Attachment:
    """
    Get the attachment for the file. If the attachment is not cached, or the file is
    newer than the cached attachment, the text content of the file will be extracted
    and the cache will be updated.
    """
    drive = _attachment_drive_for_context(context)

    with contextlib.suppress(FileNotFoundError):
        attachment = drive.read_model(Attachment, file.filename)

        if attachment.updated_datetime.astimezone(datetime.UTC) >= file.updated_datetime.astimezone(datetime.UTC):
            # if the attachment is up-to-date, return it
            return attachment

    # process the file to create an attachment
    async with context.set_status_for_block(f"updating attachment {file.filename} ..."):
        content = ""
        try:
            # read the content of the file
            file_bytes = await _read_conversation_file(context, file)
            # convert the content of the file to a string
            content = await convert.bytes_to_str(file_bytes, filename=file.filename)
        except Exception as e:
            await error_handler(context, e)

    attachment = Attachment(
        filename=file.filename, content=content, metadata=metadata, updated_datetime=file.updated_datetime
    )
    drive.write_model(attachment, file.filename)

    return attachment


def _delete_attachment_for_file(context: ConversationContext, file: File) -> None:
    drive = _attachment_drive_for_context(context)

    with contextlib.suppress(FileNotFoundError):
        drive.delete(file.filename)


def _attachment_drive_for_context(context: ConversationContext) -> Drive:
    """
    Get the Drive instance for the attachments.
    """
    drive_root = storage_directory_for_context(context) / "attachments"
    return Drive(DriveConfig(root=drive_root))


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
