# Copyright (c) Microsoft. All rights reserved.
# Generalizes message formatting and response generation for different model services

from abc import abstractmethod
from typing import Any, Iterable, List, TypeAlias, TypedDict, Union

import anthropic
import deepmerge
from google.genai.types import Content
from openai.types.chat import (
    ChatCompletion,
    ChatCompletionAssistantMessageParam,
    ChatCompletionMessage,
    ChatCompletionMessageParam,
    ChatCompletionSystemMessageParam,
    ChatCompletionUserMessageParam,
)
from openai.types.chat.chat_completion import Choice
from pydantic import BaseModel, ConfigDict

from .config import (
    AnthropicServiceConfig,
    AzureOpenAIServiceConfig,
    GeminiServiceConfig,
    OllamaServiceConfig,
    OpenAIServiceConfig,
    RequestConfig,
    ServiceType,
)


class Message:
    def __init__(self, role: str, content: str) -> None:
        self.role = role
        self.content = content


class GenerateResponseResult(BaseModel):
    response: str | None = None
    error: str | None = None
    metadata: dict[str, Any]


class ModelAdapter(BaseModel):
    model_config = ConfigDict(arbitrary_types_allowed=True)

    @abstractmethod
    def _format_messages(self, messages: List[Message]) -> Any:
        pass

    @abstractmethod
    async def generate_response(
        self, messages: List[Message], request_config: RequestConfig, service_config: Any
    ) -> GenerateResponseResult:
        pass


#
# region OpenAI
#


class OpenAIAdapter(ModelAdapter):
    def _format_messages(self, messages: List[Message]) -> List[ChatCompletionMessageParam]:
        formatted_messages = []
        for msg in messages:
            if msg.role == "system":
                formatted_messages.append(ChatCompletionSystemMessageParam(role=msg.role, content=msg.content))
            elif msg.role == "user":
                formatted_messages.append(ChatCompletionUserMessageParam(role=msg.role, content=msg.content))
            elif msg.role == "assistant":
                formatted_messages.append(ChatCompletionAssistantMessageParam(role=msg.role, content=msg.content))
            # Add other roles if necessary
        return formatted_messages

    async def generate_response(
        self,
        messages: List[Message],
        request_config: RequestConfig,
        service_config: AzureOpenAIServiceConfig | OpenAIServiceConfig | OllamaServiceConfig,
    ) -> GenerateResponseResult:
        formatted_messages = self._format_messages(messages)

        metadata: dict[str, Any] = {
            "debug": {
                "request": {
                    "messages": formatted_messages,
                    "service_type": service_config.service_type_display_name,
                    "model": service_config.openai_model,
                    "max_tokens": request_config.response_tokens,
                }
            }
        }

        try:
            async with service_config.new_client() as client:
                completion: ChatCompletion = await client.chat.completions.create(
                    messages=formatted_messages,
                    model=service_config.openai_model,
                    max_tokens=request_config.response_tokens,
                )

            choice: Choice = completion.choices[0]
            message: ChatCompletionMessage = choice.message

            deepmerge.always_merger.merge(metadata, {"debug": {"response": completion.model_dump_json()}})

            return GenerateResponseResult(
                response=message.content,
                metadata=metadata,
            )
        except Exception as e:
            return exception_to_generate_response_result(e, metadata)


# endregion

#
# region Anthropic
#


class AnthropicAdapter(ModelAdapter):
    class AnthropicFormattedMessages(TypedDict):
        system: Union[str, Iterable[anthropic.types.TextBlockParam], anthropic.NotGiven]
        messages: Iterable[anthropic.types.MessageParam]

    def _format_messages(self, messages: List[Message]) -> AnthropicFormattedMessages:
        system_messages = [msg.content for msg in messages if msg.role == "system"]
        chat_messages = []

        last_role = None
        for msg in messages:
            if msg.role == "system":
                continue

            if msg.role == last_role == "user":
                # If we have consecutive user messages, combine them
                chat_messages[-1]["content"] += f"\n\n{msg.content}"
            elif msg.role == last_role == "assistant":
                # If we have consecutive assistant messages, combine them
                chat_messages[-1]["content"] += f"\n\n{msg.content}"
            else:
                # Add the message normally if roles are alternating
                chat_messages.append({"role": msg.role, "content": msg.content})

            last_role = msg.role

        # Ensure the conversation starts with a user message
        if not chat_messages or chat_messages[0]["role"] != "user":
            chat_messages.insert(0, {"role": "user", "content": "Hello"})

        # Ensure the conversation ends with a user message
        if chat_messages[-1]["role"] != "user":
            chat_messages.append({"role": "user", "content": "Please continue."})

        return {"system": "\n\n".join(system_messages), "messages": chat_messages}

    async def generate_response(
        self,
        messages: List[Message],
        request_config: RequestConfig,
        service_config: AnthropicServiceConfig,
    ) -> GenerateResponseResult:
        formatted_messages = self._format_messages(messages)

        metadata: dict[str, Any] = {
            "debug": {
                "request": {
                    "messages": formatted_messages,
                    "service_type": service_config.service_type_display_name,
                    "model": service_config.anthropic_model,
                    "max_tokens": request_config.response_tokens,
                }
            }
        }

        try:
            async with service_config.new_client() as client:
                completion = await client.messages.create(
                    model=service_config.anthropic_model,
                    messages=formatted_messages["messages"],
                    system=formatted_messages["system"],
                    max_tokens=request_config.response_tokens,
                )

                # content is a list of ContentBlock objects, so we need to convert it to a string
                # ContentBlock is a union of TextBlock and ToolUseBlock, so we need to check for both
                # we're only expecting text blocks for now, so raise an error if we get a ToolUseBlock
                content = completion.content
                deepmerge.always_merger.merge(metadata, {"debug": {"response": completion.model_dump_json()}})
                if not isinstance(content, list):
                    return GenerateResponseResult(
                        error="Content is not a list",
                        metadata=metadata,
                    )

                for item in content:
                    if isinstance(item, anthropic.types.TextBlock):
                        return GenerateResponseResult(
                            response=item.text,
                            metadata=metadata,
                        )

                    if isinstance(item, anthropic.types.ToolUseBlock):
                        return GenerateResponseResult(
                            error="Received a ToolUseBlock, which is not supported",
                            metadata=metadata,
                        )

                return GenerateResponseResult(
                    error="Received an unexpected response",
                    metadata=metadata,
                )

        except Exception as e:
            return exception_to_generate_response_result(e, metadata)

        return GenerateResponseResult(
            error="Unexpected error",
            metadata=metadata,
        )


# endregion

#
# region Gemini
#


GeminiFormattedMessages: TypeAlias = Iterable[Content]


class GeminiAdapter(ModelAdapter):
    def _format_messages(self, messages: List[Message]) -> GeminiFormattedMessages:
        gemini_messages = []
        for msg in messages:
            if msg.role == "system":
                if gemini_messages:
                    gemini_messages[0]["parts"][0] = msg.content + "\n\n" + gemini_messages[0]["parts"][0]
                else:
                    gemini_messages.append({"role": "user", "parts": [msg.content]})
            else:
                gemini_messages.append({"role": "user" if msg.role == "user" else "model", "parts": [msg.content]})
        return gemini_messages

    async def generate_response(
        self,
        messages: List[Message],
        request_config: RequestConfig,
        service_config: GeminiServiceConfig,
    ) -> GenerateResponseResult:
        formatted_messages = self._format_messages(messages)

        metadata: dict[str, Any] = {
            "debug": {
                "request": {
                    "messages": formatted_messages,
                    "service_type": service_config.service_type_display_name,
                    "model": service_config.gemini_model,
                }
            }
        }

        try:
            client = service_config.new_client()
            chat = client.aio.chats.create(model=service_config.gemini_model, history=list(formatted_messages)[:-1])
            latest_message = list(formatted_messages)[-1]
            message = (latest_message.parts or [""])[0]
            response = await chat.send_message(message)
            deepmerge.always_merger.merge(metadata, {"debug": {"response": response.model_dump(mode="json")}})
            return GenerateResponseResult(
                response=response.text,
                metadata=metadata,
            )
        except Exception as e:
            return exception_to_generate_response_result(e, metadata)


# endregion

#
# region General
#


def get_model_adapter(service_type: ServiceType) -> ModelAdapter:
    match service_type:
        case ServiceType.AzureOpenAI | ServiceType.OpenAI | ServiceType.Ollama:
            return OpenAIAdapter()
        case ServiceType.Anthropic:
            return AnthropicAdapter()
        case ServiceType.Gemini:
            return GeminiAdapter()


def exception_to_generate_response_result(e: Exception, metadata: dict[str, Any]) -> GenerateResponseResult:
    deepmerge.always_merger.merge(
        metadata,
        {
            "error": str(e),
            "debug": {
                "response": {
                    "error": str(e),
                }
            },
        },
    )
    return GenerateResponseResult(
        error=str(e),
        metadata=metadata,
    )


# endregion
