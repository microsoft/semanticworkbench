from typing import Annotated

from guided_conversation.utils.resources import ResourceConstraint, ResourceConstraintMode, ResourceConstraintUnit
from pydantic import BaseModel, ConfigDict, Field


class ResourceConstraintDefinition(BaseModel):
    model_config = ConfigDict(
        json_schema_extra={
            "required": ["quantity", "unit", "mode"],
        },
    )

    quantity: Annotated[int, Field(title="Quantity", description="The quantity of the resource constraint.")]
    unit: Annotated[ResourceConstraintUnit, Field(title="Unit", description="Unit of the resource constraint.")]
    mode: Annotated[ResourceConstraintMode, Field(title="Mode", description="Mode of the resource constraint.")]

    def to_resource_constraint(self) -> ResourceConstraint:
        return ResourceConstraint(
            quantity=self.quantity,
            unit=self.unit,
            mode=self.mode,
        )


class GuidedConversationDefinition(BaseModel):
    model_config = ConfigDict(json_schema_extra={"required": ["rules", "resource_constraint"]})

    rules: Annotated[
        list[str],
        Field(title="Rules", description="The do's and don'ts that the agent should follow during the conversation."),
    ]

    conversation_flow: Annotated[
        str,
        Field(
            title="Conversation flow",
            description="(optional) Defines the steps of the conversation in natural language.",
        ),
    ]

    context: Annotated[
        str,
        Field(
            title="Context",
            description="(optional) Any additional information or the circumstances the agent is in that it should be aware of. It can also include the high level goal of the conversation if needed.",
        ),
    ]

    resource_constraint: Annotated[
        ResourceConstraintDefinition,
        Field(title="Resource constraint", description="Defines how the guided-conversation should be constrained."),
    ]
