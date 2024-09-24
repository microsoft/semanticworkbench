# Copyright (c) Microsoft. All rights reserved.

import asyncio
import logging
from typing import Any

from azure.ai.contentsafety import ContentSafetyClient
from azure.ai.contentsafety.models import AnalyzeTextOptions
from semantic_workbench_assistant.assistant_app import (
    ContentSafetyEvaluation, ContentSafetyEvaluationResult,
    ContentSafetyEvaluator)

from content_safety_evaluator.config import AzureContentSafetyEvaluatorConfigModel, AzureContentSafetyServiceConfigModel

logger = logging.getLogger(__name__)


# The semantic workbench app uses react-jsonschema-form for rendering
# dynamic configuration forms based on the configuration model and UI schema
# See: https://rjsf-team.github.io/react-jsonschema-form/docs/
# Playground / examples: https://rjsf-team.github.io/react-jsonschema-form/

# The UI schema can be used to customize the appearance of the form. Use
# the UISchema class to define the UI schema for specific fields in the
# configuration model.


#
# region Evaluator Implementation
#


class AzureContentSafetyEvaluator(ContentSafetyEvaluator):
    """
    An evaluator that uses the Azure Content Safety service to evaluate content safety.
    """

    def __init__(
        self, config: AzureContentSafetyEvaluatorConfigModel, config_secrets: AzureContentSafetyServiceConfigModel
    ) -> None:
        self.config = config
        self.config_secrets = config_secrets

    async def evaluate(self, content: str | list[str]) -> ContentSafetyEvaluation:
        """
        Evaluate the content for safety using the Azure Content Safety service.
        """

        # if the content is a list, join it into a single string
        text = content if isinstance(content, str) else "\n".join(content)

        # batch the content into items that are within the maximum length
        if len(text) > self.config.max_request_length:
            items = [
                text[i : i + self.config.max_request_length]  # noqa: E203
                for i in range(0, len(text), self.config.max_request_length)
            ]
        else:
            items = [text]

        # initialize the result as pass
        result = ContentSafetyEvaluationResult.Pass
        note: str | None = None

        metadata: dict[str, Any] = {
            "content_length": len(text),
            "max_request_length": self.config.max_request_length,
            "batches": [],
        }

        # evaluate each batch of content
        results = await asyncio.gather(
            *[self._evaluate_batch(batch) for batch in items],
        )

        # combine the results of evaluating each batch
        for evaluation in results:
            # add the batch evaluation to the metadata
            metadata["batches"].append(evaluation.metadata)

            # if the batch fails, the overall result is a fail
            if evaluation.result == ContentSafetyEvaluationResult.Fail:
                result = ContentSafetyEvaluationResult.Fail
                note = evaluation.note
                break

            # if the batch warns, the overall result is a warn
            if evaluation.result == ContentSafetyEvaluationResult.Warn:
                result = ContentSafetyEvaluationResult.Warn
                note = evaluation.note

        # return the evaluation result
        return ContentSafetyEvaluation(
            result=result,
            note=note,
            metadata=metadata,
        )

    async def _evaluate_batch(self, text: str) -> ContentSafetyEvaluation:
        """
        Evaluate a batch of content for safety using the Azure Content Safety service.
        """

        # send the text to the Azure Content Safety service for evaluation
        try:
            response = ContentSafetyClient(
                endpoint=self.config_secrets.azure_content_safety_endpoint,
                credential=self.config_secrets._get_azure_credentials(),
            ).analyze_text(AnalyzeTextOptions(text=text))
        except Exception as e:
            # if there is an error, return a fail result with the error message
            return ContentSafetyEvaluation(
                result=ContentSafetyEvaluationResult.Fail,
                note=f"Azure Content Safety service error: {e}",
            )

        # determine the result based on the severities of the categories
        # where the highest severity across categories determines the result
        evaluation = ContentSafetyEvaluation(
            result=ContentSafetyEvaluationResult.Pass,
            metadata={
                **response.as_dict(),
                "content_length": len(text),
            },
        )

        for text_categories_analysis in response.categories_analysis:
            # skip categories without a severity
            if text_categories_analysis.severity is None:
                continue

            # if the severity is above the fail threshold, the result is a fail
            if text_categories_analysis.severity >= self.config.fail_at_severity:
                evaluation.result = ContentSafetyEvaluationResult.Fail
                evaluation.note = f"Content safety category '{text_categories_analysis.category}' failed."
                break

            # if the severity is above the warn threshold, the result may be warn
            # but only if it does not get overridden by a higher severity category later
            if text_categories_analysis.severity >= self.config.warn_at_severity:
                evaluation.result = ContentSafetyEvaluationResult.Warn
                evaluation.note = f"Content safety category '{text_categories_analysis.category}' warned."

        # return the evaluation result
        return evaluation


# endregion
