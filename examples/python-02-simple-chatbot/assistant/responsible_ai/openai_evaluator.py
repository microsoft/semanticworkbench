# Copyright (c) Microsoft. All rights reserved.

import asyncio
import logging
from typing import Annotated, Any

import openai
from pydantic import BaseModel, Field
from semantic_workbench_assistant.assistant_app import (
    ContentSafetyEvaluation,
    ContentSafetyEvaluationResult,
    ContentSafetyEvaluator,
)

logger = logging.getLogger(__name__)


class OpenAIContentSafetyEvaluatorConfigModel(BaseModel):
    openai_api_key: Annotated[
        str,
        Field(
            title="OpenAI API Key",
            description="The API key to use for the OpenAI API.",
        ),
    ] = ""

    max_item_size: Annotated[
        int,
        Field(
            title="Maximum Item Size",
            description=(
                "The maximum size of an item to send to the OpenAI moderations endpoint, this must be less than or"
                " equal to the service's maximum (2,000 characters at the time of writing)."
            ),
        ),
    ] = 2000

    max_item_count: Annotated[
        int,
        Field(
            title="Maximum Item Count",
            description=(
                "The maximum number of items to send to the OpenAI moderations endpoint at a time, this must be less or"
                " equal to the service's maximum (32 items at the time of writing)."
            ),
        ),
    ] = 32


class OpenAIContentSafetyEvaluator(ContentSafetyEvaluator):
    """
    An evaluator that uses the OpenAI moderations endpoint to evaluate content safety.
    """

    def __init__(self, config: OpenAIContentSafetyEvaluatorConfigModel) -> None:
        self.config = config

    async def evaluate(self, content: str | list[str]) -> ContentSafetyEvaluation:
        """
        Evaluate the content for safety using the OpenAI moderations endpoint.
        """

        # if the content is a string, convert it to a list
        content_list = content if isinstance(content, list) else [content]

        # create a list of items to send to the OpenAI moderations endpoint
        # each item must be less than the maximum size
        items = []
        for content_item in content_list:
            # if the content item is too large, split it into smaller items
            if len(content_item) > self.config.max_item_size:
                for i in range(0, len(content_item), self.config.max_item_size):
                    items.append(content_item[i : i + self.config.max_item_size])  # noqa: E203
            else:
                items.append(content_item)

        # now break it down into batches of the maximum size
        batches = [
            items[i : i + self.config.max_item_count]  # noqa: E203
            for i in range(0, len(items), self.config.max_item_count)
        ]

        # initialize the result as pass
        result = ContentSafetyEvaluationResult.Pass
        note: str | None = None

        metadata: dict[str, Any] = {
            "content_length": sum(len(item) for item in items),
            "max_item_size": self.config.max_item_size,
            "max_item_count": self.config.max_item_count,
            "batches": [],
        }

        # evaluate each batch of content
        results = await asyncio.gather(
            *[self._evaluate_batch(batch) for batch in batches],
        )

        # combine the results of evaluating each batch
        for batch_result in results:
            # add the batch evaluation to the metadata
            metadata["batches"].append(batch_result.metadata)

            # if any batch result is a fail, the overall result is a fail
            if batch_result.result == ContentSafetyEvaluationResult.Fail:
                result = ContentSafetyEvaluationResult.Fail
                note = batch_result.note
                break

            # if any batch result is a warn, the overall result is a warn
            if batch_result.result == ContentSafetyEvaluationResult.Warn:
                result = ContentSafetyEvaluationResult.Warn
                note = batch_result.note

        # return the evaluation result
        return ContentSafetyEvaluation(
            result=result,
            note=note,
            metadata=metadata,
        )

    async def _evaluate_batch(self, input: list[str]) -> ContentSafetyEvaluation:
        """
        Evaluate a batch of content for safety using the OpenAI moderations endpoint.
        """

        # send the content to the OpenAI moderations endpoint for evaluation
        try:
            moderation_response = await openai.AsyncOpenAI(
                api_key=self.config.openai_api_key,
            ).moderations.create(
                input=input,
            )
        except Exception as e:
            # if there is an error, return a fail result with the error message
            return ContentSafetyEvaluation(
                result=ContentSafetyEvaluationResult.Fail,
                note=f"OpenAI moderations endpoint error: {e}",
            )

        # if any of the results are flagged, the overall result is a fail
        result = (
            ContentSafetyEvaluationResult.Fail
            if any(result.flagged for result in moderation_response.results)
            else ContentSafetyEvaluationResult.Pass
        )

        # add the moderation response to the metadata
        metadata = {**moderation_response.model_dump(), "content_length": sum(len(chunk) for chunk in input)}

        # return the evaluation result
        return ContentSafetyEvaluation(
            result=result,
            metadata=metadata,
        )
