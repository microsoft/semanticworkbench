from dataclasses import dataclass
from typing import Optional

from pydantic import BaseModel

from form_filler_skill.guided_conversation.resources import ResourceConstraint


@dataclass
class GCDefinition(BaseModel):
    artifact_schema: BaseModel
    rules: str
    conversation_flow: Optional[str]
    conversation_context: str
    resource_constraint: Optional[ResourceConstraint]


class DefaultArtifact(BaseModel):
    # TODO: Implement a guided simple guided conversation that just solicits
    # user info.
    pass


def default_gc_definition():
    # TODO: Implement a guided simple guided conversation that just solicits
    # user info.
    return GCDefinition(
        artifact_schema=DefaultArtifact(),
        rules="",
        conversation_flow="",
        conversation_context="",
        resource_constraint=None,
    )
