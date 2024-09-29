from typing import Annotated

from pydantic import BaseModel, ConfigDict, Field
from semantic_workbench_assistant.config import UISchema

from .azure_content_safety.config import AzureContentSafetyEvaluatorConfig
from .openai_moderations.config import OpenAIContentSafetyEvaluatorConfig


class CombinedContentSafetyEvaluatorConfig(BaseModel):
    model_config = ConfigDict(title="Content Safety Evaluator")

    service_config: Annotated[
        AzureContentSafetyEvaluatorConfig | OpenAIContentSafetyEvaluatorConfig,
        Field(
            title="Content Safety Evaluator",
        ),
        UISchema(widget="radio", hide_title=True),
    ] = AzureContentSafetyEvaluatorConfig()
