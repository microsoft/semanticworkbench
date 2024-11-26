from pydantic import BaseModel, Field

from form_filler_skill.guided_conversation.resources import (
    ResourceConstraintMode,
)


class AgendaItem(BaseModel):
    title: str = Field(description="Brief description of the item")
    resource: int = Field(description="Number of turns required for the item")


class Agenda(BaseModel):
    resource_constraint_mode: ResourceConstraintMode | None = Field(default=None)
    items: list[AgendaItem] = Field(
        description="Ordered list of items to be completed in the remainder of the conversation",
        default_factory=list,
    )
