# Copyright (c) Microsoft. All rights reserved.

import logging
from typing import Iterable, Sequence

import deepmerge
import openai_client
from assistant_extensions.ai_clients.config import AzureOpenAIClientConfigModel, OpenAIClientConfigModel
from assistant_extensions.ai_clients.model import CompletionMessage
from assistant_extensions.artifacts import ArtifactsExtension
from openai.types.chat import (
    ChatCompletion,
    ChatCompletionDeveloperMessageParam,
    ChatCompletionMessageParam,
    ChatCompletionUserMessageParam,
    ParsedChatCompletion,
)
from semantic_workbench_api_model.workbench_model import (
    AssistantStateEvent,
    MessageType,
)
from semantic_workbench_assistant.assistant_app import (
    ConversationContext,
)

from ..config import AssistantConfigModel
from .model import NumberTokensResult, ResponseProvider, ResponseResult

logger = logging.getLogger(__name__)


class OpenAIResponseProvider(ResponseProvider):
    def __init__(
        self,
        artifacts_extension: ArtifactsExtension,
        conversation_context: ConversationContext,
        assistant_config: AssistantConfigModel,
        openai_client_config: OpenAIClientConfigModel | AzureOpenAIClientConfigModel,
    ) -> None:
        self.artifacts_extension = artifacts_extension
        self.conversation_context = conversation_context
        self.assistant_config = assistant_config
        self.service_config = openai_client_config.service_config
        self.request_config = openai_client_config.request_config

    async def num_tokens_from_messages(
        self,
        messages: Sequence[CompletionMessage],
        model: str,
        metadata_key: str,
    ) -> NumberTokensResult:
        """
        Calculate the number of tokens in a message.
        """
        count = openai_client.num_tokens_from_messages(
            model=model, messages=openai_client.convert_from_completion_messages(messages)
        )

        return NumberTokensResult(
            count=count,
            metadata={
                "debug": {
                    metadata_key: {
                        "request": {
                            "model": model,
                            "messages": messages,
                        },
                        "response": count,
                    },
                },
            },
            metadata_key=metadata_key,
        )

    async def get_response(
        self,
        messages: list[CompletionMessage],
        metadata_key: str,
    ) -> ResponseResult:
        """
        Respond to a conversation message.

        This method uses the OpenAI API to generate a response to the message.

        It includes any attachments as individual system messages before the chat history, along with references
        to the attachments in the point in the conversation where they were mentioned. This allows the model to
        consider the full contents of the attachments separate from the conversation, but with the context of
        where they were mentioned and any relevant surrounding context such as how to interpret the attachment
        or why it was shared or what to do with it.
        """

        response_result = ResponseResult(
            content=None,
            message_type=MessageType.chat,
            metadata={},
            completion_total_tokens=0,
        )

        # define the metadata key for any metadata created within this method
        method_metadata_key = f"{metadata_key}:openai"

        # initialize variables for the response content
        completion: ParsedChatCompletion | ChatCompletion | None = None

        # convert the messages to chat completion message parameters
        chat_message_params: Iterable[ChatCompletionMessageParam] = openai_client.convert_from_completion_messages(
            messages
        )

        # generate a response from the AI model
        async with openai_client.create_client(self.service_config) as client:
            try:
                if self.request_config.is_reasoning_model:
                    # due to variations in the API response for reasoning models, we need to adjust the messages
                    # and completion request based on the model type

                    # initialize the completion parameters
                    # for reasoning models, use max_completion_tokens instead of max_tokens
                    completion_params = {
                        "model": self.request_config.model,
                        "max_completion_tokens": self.request_config.response_tokens,
                    }

                    legacy_models = ["o1-preview", "o1-mini"]

                    # set the role of the messages based on the model type
                    if self.request_config.model not in legacy_models:
                        chat_message_params = [
                            ChatCompletionDeveloperMessageParam({
                                "role": "developer",
                                "content": message["content"],
                            })
                            if message["role"] == "system"
                            else message
                            for message in chat_message_params
                        ]
                    else:
                        # fallback for older reasoning models
                        chat_message_params = [
                            ChatCompletionUserMessageParam({
                                "role": "user",
                                "content": message["content"],
                            })
                            if message["role"] == "system"
                            else message
                            for message in chat_message_params
                        ]

                    # set the reasoning effort for the completion for newer reasoning models
                    if self.request_config.model not in legacy_models:
                        completion_params["reasoning_effort"] = self.request_config.reasoning_effort

                    completion_params["messages"] = chat_message_params

                    # cast the completion to a ChatCompletion for reasoning models
                    reasoning_completion: ChatCompletion = await client.chat.completions.create(**completion_params)
                    completion = reasoning_completion

                    response_result.content = completion.choices[0].message.content

                elif self.assistant_config.extensions_config.artifacts.enabled:
                    response = await self.artifacts_extension.get_openai_completion_response(
                        client,
                        chat_message_params,
                        self.request_config.model,
                        self.request_config.response_tokens,
                    )

                    completion = response.completion
                    response_result.content = response.assistant_response
                    artifacts_to_create_or_update = response.artifacts_to_create_or_update

                    for artifact in artifacts_to_create_or_update:
                        self.artifacts_extension.create_or_update_artifact(
                            self.conversation_context,
                            artifact,
                        )
                    # send an event to notify the artifact state was updated
                    await self.conversation_context.send_conversation_state_event(
                        AssistantStateEvent(
                            state_id="artifacts",
                            event="updated",
                            state=None,
                        )
                    )
                    # send a focus event to notify the assistant to focus on the artifacts
                    await self.conversation_context.send_conversation_state_event(
                        AssistantStateEvent(
                            state_id="artifacts",
                            event="focus",
                            state=None,
                        )
                    )

                else:
                    # call the OpenAI API to generate a completion
                    if self.request_config.is_reasoning_model:
                        # for reasoning models, use max_completion_tokens instead of max_tokens
                        completion = await client.chat.completions.create(
                            messages=chat_message_params,
                            model=self.request_config.model,
                            max_completion_tokens=self.request_config.response_tokens,
                            reasoning_effort=self.request_config.reasoning_effort,
                        )
                    else:
                        completion = await client.chat.completions.create(
                            messages=chat_message_params,
                            model=self.request_config.model,
                            max_tokens=self.request_config.response_tokens,
                        )

                    response_result.content = completion.choices[0].message.content

            except Exception as e:
                logger.exception(f"exception occurred calling openai chat completion: {e}")
                response_result.content = (
                    "An error occurred while calling the OpenAI API. Is it configured correctly?"
                    " View the debug inspector for more information."
                )
                response_result.message_type = MessageType.notice
                deepmerge.always_merger.merge(
                    response_result.metadata,
                    {"debug": {method_metadata_key: {"error": str(e)}}},
                )

        if completion is not None:
            # get the total tokens used for the completion
            response_result.completion_total_tokens = completion.usage.total_tokens if completion.usage else 0

        # update the metadata with debug information
        deepmerge.always_merger.merge(
            response_result.metadata,
            {
                "debug": {
                    method_metadata_key: {
                        "request": {
                            "model": self.request_config.model,
                            "messages": chat_message_params,
                            "max_tokens": self.request_config.response_tokens,
                        },
                        "response": completion.model_dump() if completion else "[no response from openai]",
                    },
                },
            },
        )

        # send the response to the conversation
        return response_result
