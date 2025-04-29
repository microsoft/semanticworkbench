from typing import Annotated

from pydantic import BaseModel, Field
from semantic_workbench_assistant.config import UISchema

from assistant.guidance.guidance_prompts import USER_GUIDANCE_INSTRUCTIONS


class GuidanceConfigModel(BaseModel):
    enabled: Annotated[
        bool,
        Field(
            description="Enable or disable this feature.",
        ),
    ] = True

    prompt: Annotated[
        str,
        Field(
            description="The prompt that is injected at the end of the system prompt. Current dynamic UI is automatically injected at the end.",
        ),
        UISchema(widget="textarea"),
    ] = USER_GUIDANCE_INSTRUCTIONS
