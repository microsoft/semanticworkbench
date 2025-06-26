import datetime
from typing import Annotated, Any, Literal, Protocol

from pydantic import BaseModel, Field
from semantic_workbench_assistant.config import UISchema


class AttachmentsConfigModel(BaseModel):
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

    preferred_message_role: Annotated[
        Literal["system", "user"],
        Field(
            description=(
                "The preferred role for attachment messages. Early testing suggests that the system role works best,"
                " but you can experiment with the other roles. Image attachments will always use the user role."
            ),
        ),
    ] = "system"


class Attachment(BaseModel):
    filename: str
    content: str = ""
    error: str = ""
    summary: str = ""
    metadata: dict[str, Any] = {}
    updated_datetime: datetime.datetime = Field(default=datetime.datetime.fromtimestamp(0, datetime.timezone.utc))


class AttachmentSummary(BaseModel):
    """
    A model representing a summary of an attachment.
    """

    summary: str
    updated_datetime: datetime.datetime = Field(default=datetime.datetime.fromtimestamp(0, datetime.timezone.utc))


class Summarizer(Protocol):
    """
    A protocol for a summarizer that can summarize attachment content.
    """

    async def summarize(self, attachment: Attachment) -> str:
        """
        Summarize the content of the attachment.
        Returns the summary.
        """
        ...
