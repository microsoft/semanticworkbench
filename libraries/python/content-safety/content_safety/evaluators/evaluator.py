# Copyright (c) Microsoft. All rights reserved.

import logging

from content_safety.evaluators.azure_content_safety.config import AzureContentSafetyEvaluatorConfig
from content_safety.evaluators.openai_moderations.config import OpenAIContentSafetyEvaluatorConfig
from semantic_workbench_assistant.assistant_app import (
    ContentSafetyEvaluation,
    ContentSafetyEvaluator,
)

from .azure_content_safety import AzureContentSafetyEvaluator
from .config import CombinedContentSafetyEvaluatorConfig
from .openai_moderations import OpenAIContentSafetyEvaluator

logger = logging.getLogger(__name__)


class CombinedContentSafetyEvaluator(ContentSafetyEvaluator):
    """
    An evaluator that uses the Azure Content Safety service to evaluate content safety.
    """

    def __init__(self, config: CombinedContentSafetyEvaluatorConfig) -> None:
        self.config = config

    async def evaluate(self, content: str | list[str]) -> ContentSafetyEvaluation:
        """
        Evaluate the content for safety using the Azure Content Safety service.
        """

        if isinstance(self.config.service_config, AzureContentSafetyEvaluatorConfig):
            return await AzureContentSafetyEvaluator(self.config.service_config).evaluate(content)
        elif isinstance(self.config.service_config, OpenAIContentSafetyEvaluatorConfig):
            return await OpenAIContentSafetyEvaluator(self.config.service_config).evaluate(content)

        raise ValueError("Invalid service configuration.")
