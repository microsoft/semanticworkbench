import base64
import logging
import tempfile
from typing import Annotated, Any, Optional

import docx2txt
import pdfplumber
from openai.types import chat
from pydantic import BaseModel, Field
from semantic_workbench_api_model import workbench_model, workbench_service_client
from semantic_workbench_assistant.storage import FileStorage, ModelStorage

logger = logging.getLogger(__name__)


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
    metadata: Optional[dict[str, Any]]


class AttachmentAgent:
    def __init__(
        self,
        client: workbench_service_client.ConversationAPIClient,
        file_storage: FileStorage,
    ) -> None:
        self.client = client
        self.model_storage = ModelStorage(Attachment, file_storage, "attachments")

    async def content_from_docx(self, raw_content: bytes) -> str:
        with tempfile.TemporaryFile() as temp:
            temp.write(raw_content)
            temp.seek(0)
            text = docx2txt.process(temp)
        return text

    async def content_from_pdf(self, raw_content: bytes) -> str:
        with tempfile.TemporaryFile() as temp:
            temp.write(raw_content)
            temp.seek(0)
            text = ""
            with pdfplumber.open(temp) as pdf:
                for page in pdf.pages:
                    text += page.extract_text()
        return text

    async def content_from_image(self, filename: str, raw_content: bytes) -> str:
        data = base64.b64encode(raw_content).decode("utf-8")
        image_type = f"image/{filename.split('.')[-1]}"
        data_uri = f"data:{image_type};base64,{data}"
        return data_uri

    async def set_attachment_content_from_file(self, file: workbench_model.File) -> None:
        filename = file.filename
        raw_content = self.client.read_file(filename)
        contents = b""
        async with raw_content as f:
            async for chunk in f:
                contents += chunk

        supported_image_extensions = [".png", ".jpg", ".jpeg", ".gif", ".bmp", ".tiff", ".tif"]

        try:
            # if the file has .docx extension, convert it to text
            if filename.endswith(".docx"):
                content = await self.content_from_docx(contents)
            # if the file has .pdf extension, convert it to text
            elif filename.endswith(".pdf"):
                content = await self.content_from_pdf(contents)
            # if the file has an image extension, convert it to a data URI
            elif filename.endswith(tuple(supported_image_extensions)):
                content = await self.content_from_image(filename, contents)
            else:
                # otherwise, read the content as bytes and decode it
                content = contents.decode("utf-8")
        except Exception as e:
            message = f"[extracting content] {e}"
            logger.exception(message)
            raise Exception(message)

        # see if there is already an attachment with this filename
        attachment = self.model_storage.get(filename)
        if attachment:
            # if there is, update the content
            attachment.content = content
        else:
            # if there isn't, create a new attachment
            attachment = Attachment(filename=filename, content=content, metadata=None)
        self.model_storage.set(filename, attachment)

    def delete_attachment_for_file(self, file: workbench_model.File) -> None:
        filename = file.filename
        self.delete_attachment_for_filename(filename)

    def delete_attachment_for_filename(self, filename: str) -> None:
        self.model_storage.delete(filename)

    async def get_attachment(self, filename: str) -> Attachment | None:
        return self.model_storage.get(filename)

    async def get_attachments(self) -> list[Attachment]:
        return self.model_storage.get_all()

    async def generate_attachment_messages(
        self, filenames: list[str] | None = None, ignore_filenames: list[str] | None = None
    ) -> list[chat.ChatCompletionMessageParam]:
        attachments = await self.get_attachments()
        if not attachments:
            return []

        messages = []
        for attachment in attachments:
            if filenames and attachment.filename not in filenames:
                continue

            if ignore_filenames and attachment.filename in ignore_filenames:
                continue

            if attachment.content.startswith("data:image/"):
                messages.append({
                    "role": "system",
                    "content": [{
                        "type": "image_url",
                        "image_url": {
                            "url": attachment.content,
                        },
                    }],
                })
                continue

            content_details = (
                f"\n\t<FILENAME>{attachment.filename}</FILENAME>\n\t<CONTENT>{attachment.content}</CONTENT>"
            )

            if attachment.metadata:
                context = attachment.metadata.get("context")
                if context and isinstance(context, dict):
                    for context_key, context_value in context.items():
                        content_details += f"\n\t<{context_key}>{context_value}</{context_key}>"

            messages.append({
                "role": "system",
                "content": f"<ATTACHMENT>{content_details}\n</ATTACHMENT>",
            })

        return messages
