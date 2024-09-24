from typing import Annotated, Union

from pydantic import BaseModel, ConfigDict, Field
from semantic_workbench_assistant.config import UISchema

from .azure_content_safety.config import AzureContentSafetyEvaluatorConfig
from .openai_moderations.config import OpenAIContentSafetyEvaluatorConfig


class CombinedContentSafetyEvaluatorConfig(BaseModel):
    model_config = ConfigDict(title="Content Safety Evaluator Configuration")

    service_config: Annotated[
        Union[AzureContentSafetyEvaluatorConfig, OpenAIContentSafetyEvaluatorConfig],
        Field(
            title="Service Configuration",
            description="The configuration for the content safety service to use.",
        ),
        UISchema(widget="radio"),
    ] = AzureContentSafetyEvaluatorConfig()
