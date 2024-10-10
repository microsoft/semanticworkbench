import base64
import io
import logging
from typing import Annotated, Any

import docx2txt
import pdfplumber
from assistant_drive import Drive, DriveConfig
from openai.types import chat
from pydantic import BaseModel, Field
from semantic_workbench_api_model.workbench_model import File
from semantic_workbench_assistant.assistant_app import (
    ConversationContext,
    storage_directory_for_context,
)
from semantic_workbench_assistant.config import UISchema

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


attachment_tag = "ATTACHMENT"
filename_tag = "FILENAME"
content_tag = "CONTENT"
image_tag = "IMAGE"


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
        try:
            attachment = _get_attachment_drive(context).read_model(Attachment, filename)
            # if there is, update the content
            attachment.content = content
        except FileNotFoundError:
            # if there isn't, create a new attachment
            attachment = Attachment(filename=filename, content=content, metadata=metadata)

        # write the attachment to the storage
        _get_attachment_drive(context).write_model(attachment, filename)

    @staticmethod
    def delete_attachment_for_file(context: ConversationContext, file: File) -> None:
        """
        Delete the attachment for the given file.
        """

        filename = file.filename
        _get_attachment_drive(context).delete(filename)

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
        attachments = _get_attachment_drive(context).read_models(Attachment)
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
                    ],
                })
                continue

            # otherwise, include the content as text within the message content
            content_details = f"<{filename_tag}>{attachment.filename}</{filename_tag}><{content_tag}>{attachment.content}</{content_tag}>"

            messages.append({
                "role": "system",
                "content": f"<{attachment_tag}>{content_details}</{attachment_tag}>",
            })

        return messages

    @staticmethod
    def reduce_attachment_payload_from_content(value: Any) -> Any:
        """
        Reduce the content of any attachment in the payload to a smaller size.

        This method is intended to be used with the debug metadata in the parent assistant that
        uses this agent to reduce the size of the content of the attachments in the payload.

        The content will be reduced to the first and last `head_tail_length` characters, with a
        placeholder in the middle.
        """

        # define the length of the head and tail of the content to keep and the placeholder to use in the middle
        head_tail_length = 40
        placeholder = "<REDUCED_FOR_DEBUG_OUTPUT/>"

        # inspect the content and look for the attachment tags
        # there are two types of content that we need to handle: text and image
        # if the content is an image, we will be reducing the image_url.url value
        # if the content is text, we will be reducing the text value if it contains the attachment tag

        # start by checking if this is a string or a list of dictionaries
        if isinstance(value, str):
            # if this is a string, we can assume that this is a text content
            # we will be reducing the text value if it contains the attachment tag
            if attachment_tag in value:
                # just reduce within the content_tag, but still show the head/tail in there
                start_index = value.find(f"<{content_tag}>") + len(f"<{content_tag}>")
                end_index = value.find(f"</{content_tag}>")
                if start_index != -1 and end_index != -1:
                    return (
                        value[: start_index + head_tail_length]
                        + f"...{placeholder}..."
                        + value[end_index - head_tail_length :]
                    )
        elif isinstance(value, list):
            # if this is a list, check to see if it contains dictionaries
            # and if they contain the attachment tag
            # if so, look for and reduce the image_url.url value
            is_attachment = False
            for item in value:
                if isinstance(item, dict):
                    if "text" in item and attachment_tag in item["text"]:
                        is_attachment = True
                        break
            if is_attachment:
                # reduce the image_url.url value
                for item in value:
                    if isinstance(item, dict) and "image_url" in item:
                        item["image_url"]["url"] = item["image_url"]["url"][:head_tail_length] + f"...{placeholder}"
            return value

        # if the content is not an attachment, return the original value
        return value


# endregion


#
# region Helpers
#


def _get_attachment_drive(context: ConversationContext) -> Drive:
    """
    Get the Drive instance for the attachments.
    """
    drive_root = storage_directory_for_context(context) / "attachments"
    return Drive(DriveConfig(root=drive_root))


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
