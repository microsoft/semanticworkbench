from typing import Any, Optional

from pydantic import BaseModel

from .resources import ResourceConstraint


class GCDefinition(BaseModel):
    artifact_schema: dict[str, Any]
    rules: list[str]
    conversation_context: str
    conversation_flow: Optional[str] = None
    resource_constraint: Optional[ResourceConstraint] = None
