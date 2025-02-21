# Copyright (c) Microsoft. All rights reserved.

import logging
from typing import Iterable, Sequence

import anthropic_client
import deepmerge
from anthropic import NotGiven
from anthropic.types import Message, MessageParam, TextBlock, ToolUseBlock
from assistant_extensions.ai_clients.config import AnthropicClientConfigModel
from llm_client.model import CompletionMessage
from semantic_workbench_api_model.workbench_model import (
    MessageType,
)

from ..config import AssistantConfigModel
from .model import NumberTokensResult, ResponseProvider, ResponseResult

logger = logging.getLogger(__name__)


class AnthropicResponseProvider(ResponseProvider):
    def __init__(
        self,
        assistant_config: AssistantConfigModel,
        anthropic_client_config: AnthropicClientConfigModel,
    ) -> None:
        self.assistant_config = assistant_config
        self.service_config = anthropic_client_config.service_config
        self.request_config = anthropic_client_config.request_config

    async def num_tokens_from_messages(
        self,
        messages: Sequence[CompletionMessage],
        model: str,
        metadata_key: str,
    ) -> NumberTokensResult:
        """
        Calculate the number of tokens in a message.
        """

        beta_message_params = anthropic_client.beta_convert_from_completion_messages(messages)
        results = NumberTokensResult(
            count=0,
            metadata={
                "debug": {
                    metadata_key: {
                        "request": {
                            "model": model,
                            "messages": beta_message_params,
                        },
                    },
                },
            },
            metadata_key=metadata_key,
        )

        if len(beta_message_params) == 0:
            return results

        async with anthropic_client.create_client(self.service_config) as client:
            try:
                count = await client.beta.messages.count_tokens(
                    model=model,
                    messages=beta_message_params,
                )
                results.count = count.input_tokens
            except Exception as e:
                logger.exception(f"exception occurred calling openai count tokens: {e}")
                deepmerge.always_merger.merge(
                    results.metadata,
                    {"debug": {metadata_key: {"error": str(e)}}},
                )
        return results

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
        method_metadata_key = f"{metadata_key}:anthropic"

        # initialize variables for the response content and total tokens used
        response_message: Message | None = None

        # pluck first system message to send as system prompt, remove it from the list
        system_message = next((m for m in messages if m.role == "system"), None)
        system_prompt: str | NotGiven = NotGiven()
        if system_message:
            if isinstance(system_message.content, str):
                system_prompt = anthropic_client.create_system_prompt(system_message.content)
            messages.remove(system_message)

        # convert the messages to chat completion message parameters
        chat_message_params: Iterable[MessageParam] = anthropic_client.convert_from_completion_messages(messages)

        # generate a response from the AI model
        async with anthropic_client.create_client(self.service_config) as client:
            try:
                if self.assistant_config.extensions_config.artifacts.enabled:
                    raise NotImplementedError("Artifacts are not yet supported with our Anthropic support.")

                else:
                    # call the Anthropic API to generate a completion
                    response_message = await client.messages.create(
                        model=self.request_config.model,
                        max_tokens=self.request_config.response_tokens,
                        system=system_prompt,
                        messages=chat_message_params,
                    )
                    content = response_message.content

                    if not isinstance(content, list):
                        raise ValueError("Anthropic API did not return a list of messages.")

                    for item in content:
                        if isinstance(item, TextBlock):
                            response_result.content = item.text
                            continue

                        if isinstance(item, ToolUseBlock):
                            raise ValueError("Anthropic API returned a ToolUseBlock which is not yet supported.")

                        raise ValueError(f"Anthropic API returned an unexpected type: {type(item)}")

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

        if response_message is not None:
            # get the total tokens used for the completion
            response_result.completion_total_tokens = (
                response_message.usage.input_tokens + response_message.usage.output_tokens
            )

        # update the metadata with debug information
        deepmerge.always_merger.merge(
            response_result.metadata,
            {
                "debug": {
                    method_metadata_key: {
                        "request": {
                            "model": self.request_config.model,
                            "system": system_prompt,
                            "messages": chat_message_params,
                            "max_tokens": self.request_config.response_tokens,
                        },
                        "response": response_message.model_dump()
                        if response_message
                        else "[no response from anthropic]",
                    },
                },
            },
        )

        # send the response to the conversation
        return response_result
