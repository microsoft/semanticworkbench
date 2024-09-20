# Copyright (c) Microsoft. All rights reserved.
# Generalizes message formatting and response generation for different model services

import abc
from typing import Any, Dict, List, Union

import google.generativeai as genai
from anthropic import AsyncAnthropic
from openai import AsyncOpenAI
from openai.types.chat import (ChatCompletion,
                               ChatCompletionAssistantMessageParam,
                               ChatCompletionMessage,
                               ChatCompletionMessageParam,
                               ChatCompletionSystemMessageParam,
                               ChatCompletionUserMessageParam)
from openai.types.chat.chat_completion import Choice


class Message:
    def __init__(self, role: str, content: str):
        self.role = role
        self.content = content

class ModelAdapter(abc.ABC):
    @abc.abstractmethod
    def format_messages(self, messages: List[Message]) -> Any:
        pass

    @abc.abstractmethod
    async def generate_response(self, formatted_messages: Any, config: Any, config_secrets: Any) -> str:
        pass

class OpenAIAdapter(ModelAdapter):
    def format_messages(self, messages: List[Message]) -> List[ChatCompletionMessageParam]:
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

    async def generate_response(self, formatted_messages: List[ChatCompletionMessageParam], config: Any, config_secrets: Any) -> str:
        if hasattr(config_secrets.service_config, 'ollama_endpoint'):
            async with AsyncOpenAI(api_key=config_secrets.service_config.openai_api_key,
                                base_url=config_secrets.service_config.ollama_endpoint) as client:
                completion: ChatCompletion = await client.chat.completions.create(
                    messages=formatted_messages,
                    model=config_secrets.service_config.openai_model,
                    max_tokens=config.request_config.response_tokens,
                )
        else:
            async with AsyncOpenAI(api_key=config_secrets.service_config.openai_api_key,
                                base_url=config_secrets.service_config.base_url) as client:
                completion: ChatCompletion = await client.chat.completions.create(
                    messages=formatted_messages,
                    model=config_secrets.service_config.openai_model,
                    max_tokens=config.request_config.response_tokens,
                )
        choice: Choice = completion.choices[0]
        message: ChatCompletionMessage = choice.message
        return message.content or ""

class AnthropicAdapter(ModelAdapter):
    def format_messages(self, messages: List[Message]) -> Dict[str, Union[str, List[Dict[str, str]]]]:
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

        return {
            "system": "\n\n".join(system_messages),
            "messages": chat_messages
        }

    async def generate_response(self, formatted_messages: Dict[str, Union[str, List[Dict[str, str]]]], config: Any, config_secrets: Any) -> str:
        async with AsyncAnthropic(api_key=config_secrets.service_config.anthropic_api_key) as client:
            completion = await client.messages.create(
                model=config_secrets.service_config.anthropic_model,
                messages=formatted_messages["messages"],
                system=formatted_messages["system"],
                max_tokens=config.request_config.response_tokens,
            )
            # Convert the content to a string if it's a TextBlock or list of TextBlocks
            if hasattr(completion.content, 'text'):
                return completion.content.text
            elif isinstance(completion.content, list) and all(hasattr(item, 'text') for item in completion.content):
                return ' '.join(item.text for item in completion.content)
            return str(completion.content)

class GeminiAdapter(ModelAdapter):
    def format_messages(self, messages: List[Message]) -> List[Dict[str, Union[str, List[str]]]]:
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

    async def generate_response(self, formatted_messages: List[Dict[str, Union[str, List[str]]]], config: Any, config_secrets: Any) -> str:
        genai.configure(api_key=config_secrets.service_config.gemini_api_key)
        model = genai.GenerativeModel(config_secrets.service_config.gemini_model)
        chat = model.start_chat(history=formatted_messages)
        response = await chat.send_message_async(formatted_messages[-1]["parts"][0])
        return response.text

def get_model_adapter(service_type: str) -> ModelAdapter:
    adapters = {
        "OpenAI": OpenAIAdapter(),
        "Azure OpenAI": OpenAIAdapter(),
        "Ollama": OpenAIAdapter(),
        "Anthropic": AnthropicAdapter(),
        "Gemini": GeminiAdapter(),
    }
    adapter = adapters.get(service_type)
    if adapter is None:
        raise ValueError(f"Unsupported service type: {service_type}")
    return adapter