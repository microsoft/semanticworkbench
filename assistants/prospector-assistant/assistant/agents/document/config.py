from typing import Annotated

from guided_conversation.utils.resources import ResourceConstraint, ResourceConstraintMode, ResourceConstraintUnit
from pydantic import BaseModel, Field
from semantic_workbench_assistant.config import UISchema

#
# region Models
#


class ResourceConstraintConfigModel(ResourceConstraint):
    mode: Annotated[
        ResourceConstraintMode,
        Field(
            title="Resource Mode",
            description=(
                'If "exact", the agents will try to pace the conversation to use exactly the resource quantity. If'
                ' "maximum", the agents will try to pace the conversation to use at most the resource quantity.'
            ),
        ),
    ]

    unit: Annotated[
        ResourceConstraintUnit,
        Field(
            title="Resource Unit",
            description="The unit for the resource constraint.",
        ),
    ]

    quantity: Annotated[
        float,
        Field(
            title="Resource Quantity",
            description="The quantity for the resource constraint. If <=0, the resource constraint is disabled.",
        ),
    ]


class GuidedConversationConfigModel(BaseModel):
    rules: Annotated[
        list[str],
        Field(title="Rules", description="Do's and don'ts that the agent should attempt to follow"),
        UISchema(items=UISchema(widget="textarea", rows=2)),
    ]

    conversation_flow: Annotated[
        str,
        Field(
            title="Conversation Flow",
            description="A loose natural language description of the steps of the conversation",
        ),
        UISchema(widget="textarea", schema={"ui:options": {"rows": 10}}, placeholder="[optional]"),
    ]

    context: Annotated[
        str,
        Field(
            title="Context",
            description="General background context for the conversation.",
        ),
        UISchema(widget="textarea", placeholder="[optional]"),
    ]

    resource_constraint: Annotated[
        ResourceConstraintConfigModel,
        Field(
            title="Resource Constraint",
        ),
        UISchema(schema={"quantity": {"ui:widget": "updown"}}),
    ]


# endregion
