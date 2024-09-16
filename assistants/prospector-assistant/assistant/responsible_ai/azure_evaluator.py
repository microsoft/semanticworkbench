# Copyright (c) Microsoft. All rights reserved.

import asyncio
import logging
from typing import Annotated, Any, Literal

from azure.ai.contentsafety import ContentSafetyClient
from azure.ai.contentsafety.models import AnalyzeTextOptions
from azure.core.credentials import AzureKeyCredential
from azure.identity import DefaultAzureCredential
from pydantic import BaseModel, ConfigDict, Field
from semantic_workbench_assistant import config
from semantic_workbench_assistant.assistant_app import (
    ContentSafetyEvaluation,
    ContentSafetyEvaluationResult,
    ContentSafetyEvaluator,
)

logger = logging.getLogger(__name__)


class AzureContentSafetyServiceIdentityAuthConfig(BaseModel):
    model_config = ConfigDict(title="Azure identity based authentication")

    auth_method: Literal["azure-identity"] = "azure-identity"


class AzureContentSafetyServiceKeyAuthConfig(BaseModel):
    model_config = ConfigDict(
        title="API key based authentication",
        json_schema_extra={
            "required": ["azure_content_safety_service_key"],
        },
    )

    auth_method: Literal["api-key"] = "api-key"

    azure_content_safety_service_key: Annotated[
        str,
        Field(
            title="Azure Content Safety Service Key",
            description="The Azure Content Safety service key for your resource instance.",
        ),
    ] = config.first_env_var("azure_content_safety_service_key", "assistant__azure_content_safety_service_key") or ""


class AzureContentSafetyEvaluatorConfigModel(BaseModel):
    service_type: Literal["Azure OpenAI"] = "Azure OpenAI"

    auth_config: Annotated[
        AzureContentSafetyServiceIdentityAuthConfig | AzureContentSafetyServiceKeyAuthConfig,
        Field(
            title="Authentication Config",
            description="The authentication configuration to use for the Azure Content Safety service.",
        ),
    ] = AzureContentSafetyServiceIdentityAuthConfig()

    azure_content_safety_endpoint: Annotated[
        str,
        Field(
            title="Azure Content Safety Service Endpoint",
            description="The endpoint to use for the Azure Content Safety service.",
        ),
    ] = config.first_env_var("azure_content_safety_endpoint", "assistant__azure_content_safety_endpoint") or ""

    warn_at_severity: Annotated[
        Literal[0, 2, 4, 6],
        Field(
            title="Warn at Severity",
            description="The severity level (0, 2, 4, 6) at which to warn about content safety.",
        ),
    ] = 2

    fail_at_severity: Annotated[
        Literal[0, 2, 4, 6],
        Field(
            title="Fail at Severity",
            description="The severity level (0, 2, 4, 6) at which to fail content safety.",
        ),
    ] = 4

    max_request_length: Annotated[
        int,
        Field(
            title="Maximum Request Length",
            description=(
                "The maximum length of content to send to the Azure Content Safety service per request, this must less"
                " or equal to the service's maximum (10,000 characters at the time of writing). The evaluator will"
                " split and send the content in batches if it exceeds this length."
            ),
        ),
    ] = 10000

    # set on the class to avoid re-authenticating for each request
    def _get_azure_credentials(self):
        match self.auth_config.auth_method:
            case "api-key":
                return AzureKeyCredential(self.auth_config.azure_content_safety_service_key)

            case "azure-identity":
                return DefaultAzureCredential()


azure_content_safety_evaluator_ui_schema = {
    "service_type": {
        "ui:widget": "hidden",
    },
    "auth_config": {
        "ui:widget": "radio",
        "ui:options": {
            "hide_title": True,
        },
        "auth_method": {
            "ui:widget": "hidden",
        },
        "azure_content_safety_service_key": {
            "ui:widget": "password",
            "ui:placeholder": "[optional]",
        },
    },
}


class AzureContentSafetyEvaluator(ContentSafetyEvaluator):
    """
    An evaluator that uses the Azure Content Safety service to evaluate content safety.
    """

    def __init__(self, config: AzureContentSafetyEvaluatorConfigModel) -> None:
        self.config = config

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
                endpoint=self.config.azure_content_safety_endpoint,
                credential=self.config._get_azure_credentials(),
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
