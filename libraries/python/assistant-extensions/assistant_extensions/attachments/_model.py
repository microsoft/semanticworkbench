import datetime
from typing import Annotated, Any

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
    content: str = ""
    error: str = ""
    metadata: dict[str, Any] = {}
    updated_datetime: datetime.datetime = Field(default=datetime.datetime.fromtimestamp(0, datetime.timezone.utc))
