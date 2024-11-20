import logging

from pydantic import Field

from form_filler_skill.guided_conversation.chat_drivers.unneeded.base_model_llm import BaseModelLLM
from form_filler_skill.guided_conversation.resources import (
    ResourceConstraintMode,
)

logger = logging.getLogger(__name__)


class AgendaItem(BaseModelLLM):
    title: str = Field(description="Brief description of the item")
    resource: int = Field(description="Number of turns required for the item")


class Agenda(BaseModelLLM):
    resource_constraint_mode: ResourceConstraintMode | None = Field(default=None)
    items: list[AgendaItem] = Field(
        description="Ordered list of items to be completed in the remainder of the conversation",
        default_factory=list,
    )
