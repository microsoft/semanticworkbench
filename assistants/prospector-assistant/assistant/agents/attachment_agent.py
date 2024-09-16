import base64
import logging
import tempfile
from pathlib import Path
from typing import Annotated, Any

import docx2txt
import pdfplumber
from openai.types import chat
from pydantic import BaseModel, Field
from semantic_workbench_api_model.workbench_model import File
from semantic_workbench_assistant.assistant_app import (
    ConversationContext,
    FileStorageContext,
)
from semantic_workbench_assistant.storage import (
    model_delete,
    model_read,
    model_read_all_files,
    model_write,
)

logger = logging.getLogger(__name__)


#
# region Models
#


class AttachmentAgentConfigModel(BaseModel):
    context_description: Annotated[
        str,
        Field(
            description="The description of the context for general response generation.",
        ),
    ] = (
        "These attachments were provided for additional context to accompany the conversation. Consider any rationale"
        " provided for why they were included."
    )

    include_in_response_generation: Annotated[
        bool,
        Field(
            description=(
                "Whether to include the contents of attachments in the context for general response generation."
            ),
        ),
    ] = True


attachment_agent_config_ui_schema = {
    "context_description": {
        "ui:widget": "textarea",
    },
}


class Attachment(BaseModel):
    filename: str
    content: str
    metadata: dict[str, Any]


# endregion


#
# region Agent
#


class AttachmentAgent:
    async def create_or_update_attachment_from_file(
        self, context: ConversationContext, file: File, metadata: dict[str, Any]
    ) -> None:
        """
        Create or update an attachment from the given file.
        """
        filename = file.filename

        # get the content of the file and convert it to a string
        content = await _file_to_str(context, file)

        # see if there is already an attachment with this filename
        attachment = await _get(context, filename)
        if attachment:
            # if there is, update the content
            attachment.content = content
        else:
            # if there isn't, create a new attachment
            attachment = Attachment(filename=filename, content=content, metadata=metadata)
        await _set(context, filename, attachment)

    async def delete_attachment_for_file(self, context: ConversationContext, file: File) -> None:
        """
        Delete the attachment for the given file.
        """
        await self.delete_attachment_for_filename(context, file.filename)

    async def delete_attachment_for_filename(self, context: ConversationContext, filename: str) -> None:
        await _delete(context, filename)

    async def generate_attachment_messages(
        self,
        context: ConversationContext,
        filenames: list[str] | None = None,
        ignore_filenames: list[str] | None = None,
    ) -> list[chat.ChatCompletionMessageParam]:
        """
        Generate systems messages for each attachment that includes the filename and content.

        In the case of images, the content will be a data URI, other file types will be included as text.

        If filenames are provided, only attachments with those filenames will be included.

        If ignore_filenames are provided, attachments with those filenames will be excluded.
        """

        # get all attachments and exit early if there are none
        attachments = await _get_all(context)
        if not attachments:
            return []

        # process each attachment
        messages = []
        for attachment in attachments:
            # if filenames are provided, only include attachments with those filenames
            if filenames and attachment.filename not in filenames:
                continue

            # if ignore_filenames are provided, exclude attachments with those filenames
            if ignore_filenames and attachment.filename in ignore_filenames:
                continue

            # if the content is a data URI, include it as an image type within the message content
            if attachment.content.startswith("data:image/"):
                messages.append({
                    "role": "system",
                    "content": [
                        {
                            "type": "text",
                            "text": f"<ATTACHMENT>\n\t<FILENAME>{attachment.filename}</FILENAME>\n\t<IMAGE>",
                        },
                        {
                            "type": "image_url",
                            "image_url": {
                                "url": attachment.content,
                            },
                        },
                        {
                            "type": "text",
                            "text": "</IMAGE>\n</ATTACHMENT>",
                        },
                    ],
                })
                continue

            # otherwise, include the content as text within the message content
            content_details = (
                f"\n\t<FILENAME>{attachment.filename}</FILENAME>\n\t<CONTENT>{attachment.content}</CONTENT>"
            )

            messages.append({
                "role": "system",
                "content": f"<ATTACHMENT>{content_details}\n</ATTACHMENT>",
            })

        return messages


# endregion


#
# region Helpers
#


def _assistant_conversation_storage_directory(context: ConversationContext) -> Path:
    """
    Get the storage path for the attachments.
    """
    return FileStorageContext.get(context.assistant).directory / context.id


async def _get(context: ConversationContext, filename: str) -> Attachment | None:
    """
    Get the attachment with the given filename.
    """
    return model_read(_assistant_conversation_storage_directory(context) / filename, Attachment)


async def _get_all(context: ConversationContext) -> list[Attachment]:
    """
    Get all attachments.
    """
    return list(model_read_all_files(_assistant_conversation_storage_directory(context), Attachment))


async def _set(context: ConversationContext, filename: str, attachment: Attachment) -> None:
    """
    Set the attachment with the given filename.
    """
    model_write(_assistant_conversation_storage_directory(context) / filename, attachment)


async def _delete(context: ConversationContext, filename: str) -> None:
    """
    Delete the attachment with the given filename.
    """
    model_delete(_assistant_conversation_storage_directory(context) / filename)


async def _raw_content_from_file(context: ConversationContext, file: File) -> bytes:
    """
    Read the content of the file with the given filename.
    """
    raw_content = context.read_file(file.filename)
    content = b""
    async with raw_content as f:
        async for chunk in f:
            content += chunk
    return content


async def _docx_raw_content_to_str(raw_content: bytes, filename: str) -> str:
    """
    Convert the raw content of a DOCX file to text.
    """
    try:
        with tempfile.TemporaryFile() as temp:
            temp.write(raw_content)
            temp.seek(0)
            text = docx2txt.process(temp)
        return text
    except Exception as e:
        message = f"error converting DOCX {filename} to text: {e}"
        logger.exception(message)
        raise Exception(message)


async def _pdf_raw_content_to_str(raw_content: bytes, filename: str) -> str:
    """
    Convert the raw content of a PDF file to text.
    """
    try:
        with tempfile.TemporaryFile() as temp:
            temp.write(raw_content)
            temp.seek(0)
            text = ""
            with pdfplumber.open(temp) as pdf:
                for page in pdf.pages:
                    text += page.extract_text()
        return text
    except Exception as e:
        message = f"error converting PDF {filename} to text: {e}"
        logger.exception(message)
        raise Exception(message)


async def _image_raw_content_to_str(raw_content: bytes, filename: str) -> str:
    """
    Convert the raw content of an image file to a data URI.
    """
    try:
        data = base64.b64encode(raw_content).decode("utf-8")
        image_type = f"image/{filename.split('.')[-1]}"
        data_uri = f"data:{image_type};base64,{data}"
        return data_uri
    except Exception as e:
        message = f"error converting image {filename} to data URI: {e}"
        logger.exception(message)
        raise Exception(message)


async def _unknown_raw_content_to_str(raw_content: bytes, filename: str) -> str:
    """
    Convert the raw content of an unknown file type to a string.
    """
    try:
        return raw_content.decode("utf-8")
    except Exception as e:
        message = f"error converting unknown file type {filename} to text: {e}"
        logger.exception(message)
        raise Exception


async def _file_to_str(context: ConversationContext, file: File) -> str:
    """
    Convert the content of the file to a string.
    """
    filename = file.filename
    raw_content = await _raw_content_from_file(context, file)

    filename_extension = filename.split(".")[-1]

    match filename_extension:
        # if the file has .docx extension, convert it to text
        case "docx":
            content = await _docx_raw_content_to_str(raw_content, filename)

        # if the file has .pdf extension, convert it to text
        case "pdf":
            content = await _pdf_raw_content_to_str(raw_content, filename)

        # if the file has an image extension, convert it to a data URI
        case _ if filename_extension in ["png", "jpg", "jpeg", "gif", "bmp", "tiff", "tif"]:
            content = await _image_raw_content_to_str(raw_content, filename)

        # otherwise, try to convert the file to text
        case _:
            content = await _unknown_raw_content_to_str(raw_content, filename)

    return content


# endregion
