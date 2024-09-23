import base64
import io
import logging
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
from semantic_workbench_assistant.config import UISchema
from semantic_workbench_assistant.storage import (
    read_model,
    read_models_in_dir,
    write_model,
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
        UISchema(widget="textarea"),
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


class Attachment(BaseModel):
    filename: str
    content: str
    metadata: dict[str, Any]


# endregion


#
# region Agent
#


class AttachmentAgent:
    @staticmethod
    async def create_or_update_attachment_from_file(
        context: ConversationContext, file: File, metadata: dict[str, Any]
    ) -> None:
        """
        Create or update an attachment from the given file.
        """
        filename = file.filename

        # get the content of the file and convert it to a string
        content = await _file_to_str(context, file)

        # see if there is already an attachment with this filename
        attachment = read_model(_get_attachment_storage_path(context, filename), Attachment)
        if attachment:
            # if there is, update the content
            attachment.content = content
        else:
            # if there isn't, create a new attachment
            attachment = Attachment(filename=filename, content=content, metadata=metadata)

        write_model(_get_attachment_storage_path(context, filename), attachment)

    @staticmethod
    def delete_attachment_for_file(context: ConversationContext, file: File) -> None:
        """
        Delete the attachment for the given file.
        """

        filename = file.filename
        _get_attachment_storage_path(context, filename).unlink(missing_ok=True)

    @staticmethod
    def generate_attachment_messages(
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
        attachments = read_models_in_dir(_get_attachment_storage_path(context), Attachment)
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
            # NOTE: newer versions of the API only allow messages with the user role to include images
            if attachment.content.startswith("data:image/"):
                messages.append({
                    "role": "user",
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


def _get_attachment_storage_path(context: ConversationContext, filename: str | None = None) -> Path:
    """
    Get the path where attachments are stored.
    """
    path = FileStorageContext.get(context).directory / "attachments"
    if filename:
        path /= filename
    return path


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


def _docx_raw_content_to_str(raw_content: bytes, filename: str) -> str:
    """
    Convert the raw content of a DOCX file to text.
    """
    try:
        with io.BytesIO(raw_content) as temp:
            text = docx2txt.process(temp)
        return text
    except Exception as e:
        message = f"error converting DOCX {filename} to text: {e}"
        logger.exception(message)
        raise Exception(message)


def _pdf_raw_content_to_str(raw_content: bytes, filename: str) -> str:
    """
    Convert the raw content of a PDF file to text.
    """
    try:
        with io.BytesIO(raw_content) as temp:
            text = ""
            with pdfplumber.open(temp) as pdf:
                for page in pdf.pages:
                    text += page.extract_text()
        return text
    except Exception as e:
        message = f"error converting PDF {filename} to text: {e}"
        logger.exception(message)
        raise Exception(message)


def _image_raw_content_to_str(raw_content: bytes, filename: str) -> str:
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


def _unknown_raw_content_to_str(raw_content: bytes, filename: str) -> str:
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
            content = _docx_raw_content_to_str(raw_content, filename)

        # if the file has .pdf extension, convert it to text
        case "pdf":
            content = _pdf_raw_content_to_str(raw_content, filename)

        # if the file has an image extension, convert it to a data URI
        case _ if filename_extension in ["png", "jpg", "jpeg", "gif", "bmp", "tiff", "tif"]:
            content = _image_raw_content_to_str(raw_content, filename)

        # otherwise, try to convert the file to text
        case _:
            content = _unknown_raw_content_to_str(raw_content, filename)

    return content


# endregion
