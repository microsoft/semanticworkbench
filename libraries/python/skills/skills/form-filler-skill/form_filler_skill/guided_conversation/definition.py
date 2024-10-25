from dataclasses import dataclass
from typing import Optional

from form_filler_skill.guided_conversation.resources import ResourceConstraint


@dataclass
class GCDefinition:
    artifact_schema: str
    rules: str
    conversation_flow: Optional[str]
    conversation_context: str
    resource_constraint: Optional[ResourceConstraint]
    service_id: str = "gc_main"
