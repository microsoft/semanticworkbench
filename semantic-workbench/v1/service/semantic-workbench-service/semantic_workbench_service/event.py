from typing import Literal

from pydantic import BaseModel
from semantic_workbench_api_model.workbench_model import ConversationEvent


class ConversationEventQueueItem(BaseModel):
    event: ConversationEvent
    event_audience: set[Literal["user", "assistant"]] = set(["user", "assistant"])
