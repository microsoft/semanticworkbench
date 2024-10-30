from typing import Annotated

from guided_conversation.utils.resources import ResourceConstraint
from pydantic import BaseModel, Field


class GuidedConversationDefinition(BaseModel):
    rules: Annotated[
        list[str],
        Field(title="Rules", description="Do's and don'ts that the agent should attempt to follow"),
    ] = []

    conversation_flow: Annotated[
        str,
        Field(
            title="Conversation Flow",
            description="A loose natural language description of the steps of the conversation",
        ),
    ] = ""

    context: Annotated[
        str,
        Field(
            title="Context",
            description="General background context for the conversation.",
        ),
    ] = ""

    resource_constraint: Annotated[
        ResourceConstraint,
        Field(
            title="Resource Constraint",
        ),
    ]

    artifact: type[BaseModel]
