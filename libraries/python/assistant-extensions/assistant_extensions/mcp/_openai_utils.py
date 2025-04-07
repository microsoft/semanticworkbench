import logging
from typing import Any, Callable, List, Union

import deepmerge
from mcp import ClientSession, CreateMessageResult, SamplingMessage
from mcp.shared.context import RequestContext
from mcp.types import (
    CreateMessageRequestParams,
    ErrorData,
    ImageContent,
    ModelPreferences,
    TextContent,
)
from openai.types.chat import (
    ChatCompletion,
    ChatCompletionAssistantMessageParam,
    ChatCompletionContentPartImageParam,
    ChatCompletionMessageParam,
    ChatCompletionSystemMessageParam,
    ChatCompletionToolParam,
    ChatCompletionUserMessageParam,
)
from openai_client import OpenAIRequestConfig, create_client

from ..ai_clients.config import AzureOpenAIClientConfigModel, OpenAIClientConfigModel
from ._model import MCPSamplingMessageHandler
from ._sampling_handler import SamplingHandler

logger = logging.getLogger(__name__)

# FIXME: add metadata/debug data to entire flow
# FIXME: investigate blocking issue that causes the sampling request to wait for something else to finish
# For now it does work, but it takes much longer than it should and shows the assistant as offline while
# it does - merging before investigating to unblock others who are waiting on the first version of this.
# It works ok in office server but not giphy, so it is likely a server issue.

OpenAIMessageProcessor = Callable[
    [List[SamplingMessage]],
    List[ChatCompletionMessageParam],
]


class OpenAISamplingHandler(SamplingHandler):
    @property
    def message_handler(self) -> MCPSamplingMessageHandler:
        return self._message_handler

    def __init__(
        self,
        ai_client_configs: list[Union[AzureOpenAIClientConfigModel, OpenAIClientConfigModel]],
        assistant_mcp_tools: list[ChatCompletionToolParam] | None = None,
        message_processor: OpenAIMessageProcessor | None = None,
        handler: MCPSamplingMessageHandler | None = None,
    ) -> None:
        self.ai_client_configs = ai_client_configs
        self.assistant_mcp_tools = assistant_mcp_tools

        # set a default message processor that converts sampling messages to
        # chat completion messages and performs any necessary transformations
        # such as injecting content as replacements for placeholders, etc.
        self.message_processor: OpenAIMessageProcessor = message_processor or self._default_message_processor

        # set a default handler so that it can be registered during client
        # session connection, prior to having access to the actual handler
        # allowing the handler to be set after the client session is created
        # and more context is available
        self._message_handler: MCPSamplingMessageHandler = handler or self._default_message_handler

    def _default_message_processor(self, messages: List[SamplingMessage]) -> List[ChatCompletionMessageParam]:
        """
        Default template processor that passes messages through.
        """
        return [sampling_message_to_chat_completion_message(message) for message in messages]

    async def _default_message_handler(
        self,
        context: RequestContext[ClientSession, Any],
        params: CreateMessageRequestParams,
    ) -> CreateMessageResult | ErrorData:
        logger.info(f"Sampling handler invoked with context: {context}")

        ai_client_config = self._ai_client_config_from_model_preferences(params.modelPreferences)

        if not ai_client_config:
            raise ValueError("No AI client configs defined for sampling requests.")

        completion_args = await self._create_completion_request(
            request=params,
            request_config=ai_client_config.request_config,
            template_processor=self.message_processor,
        )

        completion: ChatCompletion | None = None
        async with create_client(ai_client_config.service_config) as client:
            completion = await client.chat.completions.create(**completion_args)

        if completion is None:
            return ErrorData(
                code=500,
                message="No completion returned from OpenAI.",
            )

        choice = completion.choices[0]
        content = choice.message.content
        if content is None:
            content = "[no content]"

        return CreateMessageResult(
            role="assistant",
            content=TextContent(
                type="text",
                text=content,
            ),
            model=completion.model,
            stopReason=choice.finish_reason,
            _meta={
                "request": completion_args,
                "response": completion.model_dump(mode="json"),
            },
        )

    async def handle_message(
        self,
        context: RequestContext[ClientSession, Any],
        params: CreateMessageRequestParams,
    ) -> CreateMessageResult | ErrorData:
        try:
            return await self._message_handler(context, params)
        except Exception as e:
            logger.error(f"Error handling sampling request: {e}")
            code = getattr(e, "status_code", 500)
            message = getattr(e, "message", "Error handling sampling request.")
            data = str(e)
            return ErrorData(code=code, message=message, data=data)

    def _ai_client_config_from_model_preferences(
        self, model_preferences: ModelPreferences | None
    ) -> Union[AzureOpenAIClientConfigModel, OpenAIClientConfigModel] | None:
        """
        Returns an AI client config from model preferences.
        """

        # if no configs are provided, return None
        if not self.ai_client_configs or len(self.ai_client_configs) == 0:
            return None

        # if not provided, return the first config
        if not model_preferences:
            return self.ai_client_configs[0]

        # if hints are provided, return the first hint where the name value matches
        # the start of the model name
        if model_preferences.hints:
            for hint in model_preferences.hints:
                if not hint.name:
                    continue
                for ai_client_config in self.ai_client_configs:
                    if ai_client_config.request_config.model.startswith(hint.name):
                        return ai_client_config

        # if any of the priority values are set, return the first config that matches our
        # criteria: speedPriority equates to non-reasoning models, intelligencePriority
        # equates to reasoning models for now
        # note: we are ignoring costPriority for now
        speed_priority = model_preferences.speedPriority or 0
        intelligence_priority = model_preferences.intelligencePriority or 0
        # cost_priority = 0 # ignored for now

        # later we will support more than just reasoning or non-reasoning choices, but
        # for now we can keep it simple
        use_reasoning_model = intelligence_priority > speed_priority

        for ai_client_config in self.ai_client_configs:
            if ai_client_config.request_config.is_reasoning_model == use_reasoning_model:
                return ai_client_config

        # failing to find a config via preferences, return first config
        return self.ai_client_configs[0]

    async def _create_completion_request(
        self,
        request: CreateMessageRequestParams,
        request_config: OpenAIRequestConfig,
        template_processor: OpenAIMessageProcessor,
    ) -> dict:
        """
        Creates a completion request.
        """

        messages: list[ChatCompletionMessageParam] = []

        # Add system prompt if provided
        if request.systemPrompt:
            messages.append(
                ChatCompletionSystemMessageParam(
                    role="system",
                    content=request.systemPrompt,
                )
            )
        # Add sampling messages
        messages += template_processor(request.messages)

        # TODO: not yet, but we can provide an option for running tools at the assistant
        # level and then pass the results to in the results
        # tools = self._assistant_mcp_tools
        # for now:
        tools = None

        # Build the completion arguments, adding tools if provided
        completion_args: dict = {
            "messages": messages,
            "model": request_config.model,
            "tools": tools,
        }

        # Allow overriding completion arguments with extra_args from metadata
        # This is useful for experimentation and is a use-at-your-own-risk feature
        if (
            request.metadata is not None
            and "extra_args" in request.metadata
            and isinstance(request.metadata["extra_args"], dict)
        ):
            completion_args = deepmerge.always_merger.merge(
                completion_args,
                request.metadata["extra_args"],
            )

        return completion_args


def openai_template_processor(
    value: SamplingMessage,
) -> Union[SamplingMessage, List[SamplingMessage]]:
    """
    Processes a SamplingMessage using OpenAI's template processor.
    """

    return value


def sampling_message_to_chat_completion_user_message(
    sampling_message: SamplingMessage,
) -> ChatCompletionUserMessageParam:
    """
    Converts a SamplingMessage to a ChatCompletionUserMessage.
    """

    if sampling_message.role != "user":
        raise ValueError(f"Unsupported role: {sampling_message.role}")

    if isinstance(sampling_message.content, TextContent):
        return ChatCompletionUserMessageParam(role="user", content=sampling_message.content.text)
    elif isinstance(sampling_message.content, ImageContent):
        return ChatCompletionUserMessageParam(
            role="user",
            content=[
                ChatCompletionContentPartImageParam(
                    type="image_url",
                    image_url={
                        "url": sampling_message.content.data,
                        "detail": "high",
                    },
                )
            ],
        )
    else:
        raise ValueError(f"Unsupported content type: {type(sampling_message.content)}")


def sampling_message_to_chat_completion_assistant_message(
    sampling_message: SamplingMessage,
) -> ChatCompletionAssistantMessageParam:
    """
    Converts a SamplingMessage to a ChatCompletionAssistantMessage.
    """
    if sampling_message.role != "assistant":
        raise ValueError(f"Unsupported role: {sampling_message.role}")

    if not isinstance(sampling_message.content, TextContent):
        raise ValueError(f"Unsupported content type: {type(sampling_message.content)} for assistant")

    return ChatCompletionAssistantMessageParam(
        role="assistant",
        content=sampling_message.content.text,
    )


def sampling_message_to_chat_completion_message(
    sampling_message: SamplingMessage,
) -> ChatCompletionMessageParam:
    """
    Converts a SamplingMessage to ChatCompletionMessageParam
    """

    match sampling_message.role:
        case "user":
            return sampling_message_to_chat_completion_user_message(sampling_message)
        case "assistant":
            return sampling_message_to_chat_completion_assistant_message(sampling_message)
        case _:
            raise ValueError(f"Unsupported role: {sampling_message.role}")
