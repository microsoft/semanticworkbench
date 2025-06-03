# Copyright (c) Microsoft. All rights reserved.

import logging
from typing import List, Literal, Union

from assistant_extensions.ai_clients.config import AzureOpenAIClientConfigModel, OpenAIClientConfigModel
from openai import AsyncOpenAI, NotGiven
from openai.types.chat import (
    ChatCompletion,
    ChatCompletionMessageParam,
    ChatCompletionToolParam,
    ParsedChatCompletion,
)
from openai_client import AzureOpenAIServiceConfig, OpenAIRequestConfig, OpenAIServiceConfig
from pydantic import BaseModel

from ...config import AssistantConfigModel

logger = logging.getLogger(__name__)


def get_ai_client_configs(
    config: AssistantConfigModel, request_type: Literal["generative", "reasoning"] = "generative"
) -> Union[AzureOpenAIClientConfigModel, OpenAIClientConfigModel]:
    def create_ai_client_config(
        service_config: AzureOpenAIServiceConfig | OpenAIServiceConfig,
        request_config: OpenAIRequestConfig,
    ) -> AzureOpenAIClientConfigModel | OpenAIClientConfigModel:
        if isinstance(service_config, AzureOpenAIServiceConfig):
            return AzureOpenAIClientConfigModel(
                service_config=service_config,
                request_config=request_config,
            )

        return OpenAIClientConfigModel(
            service_config=service_config,
            request_config=request_config,
        )

    if request_type == "reasoning":
        return create_ai_client_config(
            config.reasoning_ai_client_config.service_config,
            config.reasoning_ai_client_config.request_config,
        )

    return create_ai_client_config(
        config.generative_ai_client_config.service_config,
        config.generative_ai_client_config.request_config,
    )


async def get_completion(
    client: AsyncOpenAI,
    request_config: OpenAIRequestConfig,
    chat_message_params: List[ChatCompletionMessageParam],
    tools: List[ChatCompletionToolParam],
) -> ParsedChatCompletion[BaseModel] | ChatCompletion:
    """
    Generate a completion from the OpenAI API.
    """

    completion_args = {
        "messages": chat_message_params,
        "model": request_config.model,
    }

    if request_config.is_reasoning_model:
        # reasoning models
        completion_args["max_completion_tokens"] = request_config.response_tokens
        completion_args["reasoning_effort"] = request_config.reasoning_effort

    else:
        # all other models
        completion_args["max_tokens"] = request_config.response_tokens

    # list of models that do not support tools
    no_tools_support = ["o1-preview", "o1-mini"]
    no_parallel_tool_calls = ["o3-mini"]

    # add tools to completion args if model supports tools
    if request_config.model not in no_tools_support:
        completion_args["tools"] = tools or NotGiven()
        if tools:
            completion_args["tool_choice"] = "auto"

            if request_config.model not in no_parallel_tool_calls:
                completion_args["parallel_tool_calls"] = False

    logger.debug(
        "Initiating OpenAI request: %s for '%s' with %d messages",
        client.base_url,
        request_config.model,
        len(chat_message_params),
    )
    completion = await client.chat.completions.create(**completion_args)
    return completion
