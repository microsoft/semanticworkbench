import logging
from typing import Any, Iterable

from mcp import ClientSession, CreateMessageResult, SamplingMessage
from mcp.shared.context import RequestContext
from mcp.types import CreateMessageRequestParams, ErrorData, ImageContent, TextContent
from openai.types.chat import (
    ChatCompletion,
    ChatCompletionAssistantMessageParam,
    ChatCompletionContentPartImageParam,
    ChatCompletionContentPartParam,
    ChatCompletionMessageParam,
    ChatCompletionSystemMessageParam,
    ChatCompletionToolParam,
    ChatCompletionUserMessageParam,
)
from openai_client import OpenAIRequestConfig, ServiceConfig, create_client

logger = logging.getLogger(__name__)


# FIXME: add metadata/debug data to entire flow
# FIXME: investigate blocking issue that causes the sampling request to wait for something else to finish
# For now it does work, but it takes much longer than it should and shows the assistant as offline while
# it does - merging before investigating to unblock others who are waiting on the first version of this.


class SamplingHandler:
    def __init__(self) -> None:
        self.service_config: ServiceConfig | None = None
        self.request_config: OpenAIRequestConfig | None = None
        self.mcp_tools: list[ChatCompletionToolParam] | None = None

        async def sampling_handler(
            context: RequestContext[ClientSession, Any],
            params: CreateMessageRequestParams,
        ) -> CreateMessageResult | ErrorData:
            logger.info(
                f"Sampling handler invoked with context: {context}, params: {params}"
            )

            if not self.service_config or not self.request_config:
                raise ValueError(
                    "Service config and request config must be set before handling messages."
                )

            completion = await self._process_sampling_request(
                request=params,
                service_config=self.service_config,
                request_config=self.request_config,
            )

            content = completion.choices[0].message.content
            if content is None:
                content = "[no content]"
            logger.info(f"Received content: {content}")

            # Return a dummy result; adjust the return value to conform to CreateMessageResult | ErrorData as needed.
            return CreateMessageResult(
                role="assistant",
                content=TextContent(
                    type="text",
                    text=content,
                ),
                model="gpt-3.5-turbo",
                stopReason="stopSequence",
            )

        self.handle_message = sampling_handler

    def set_service_config(self, service_config: ServiceConfig) -> None:
        self.service_config = service_config
        logging.info(f"Set service config: {service_config}")

    def set_request_config(self, request_config: OpenAIRequestConfig) -> None:
        self.request_config = request_config
        logging.info(f"Set request config: {request_config}")

    def set_mcp_tools(
        self, mcp_tools: list[ChatCompletionToolParam] | None = None
    ) -> None:
        self.mcp_tools = mcp_tools
        logging.info(f"Set MCP tools: {mcp_tools}")

    async def _process_sampling_request(
        self,
        request: CreateMessageRequestParams,
        service_config: ServiceConfig,
        request_config: OpenAIRequestConfig,
    ) -> ChatCompletion:
        """
        Processes a sampling request.
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
        try:
            messages += sampling_messages_to_chat_completion_messages(request.messages)
        except Exception as e:
            # FIXME: add better error handling and ensure it is surfaced to the caller
            logger.exception(f"exception occurred converting sampling messages: {e}")

        # Build the completion arguments, adding tools if provided
        completion_args = {
            "messages": messages,
            "model": request_config.model,
            "tools": self.mcp_tools,
        }

        async with create_client(service_config) as client:
            try:
                completion: ChatCompletion = await client.chat.completions.create(
                    **completion_args
                )
                return completion
            except Exception as e:
                logger.exception(
                    f"exception occurred calling openai chat completion: {e}"
                )
                raise e


def sampling_message_to_chat_completion_user_message(
    sampling_message: SamplingMessage,
) -> ChatCompletionUserMessageParam | None:
    """
    Converts a SamplingMessage to a ChatCompletionUserMessage.
    """

    content: str | Iterable[ChatCompletionContentPartParam] | None = None

    if sampling_message.role != "user" or sampling_message.content is None:
        return content

    if isinstance(sampling_message.content, TextContent):
        content = sampling_message.content.text
    elif isinstance(sampling_message.content, ImageContent):
        content = [
            ChatCompletionContentPartImageParam(
                type="image_url",
                image_url={
                    "url": sampling_message.content.data,
                    "detail": "high",
                },
            )
        ]
    else:
        raise ValueError(f"Unsupported content type: {type(sampling_message.content)}")

    if content is None:
        return None

    return ChatCompletionUserMessageParam(
        role="user",
        content=content,
    )


def sampling_message_to_chat_completion_assistant_message(
    sampling_message: SamplingMessage,
) -> ChatCompletionAssistantMessageParam | None:
    """
    Converts a SamplingMessage to a ChatCompletionAssistantMessage.
    """
    content: str | None = None

    if sampling_message.role != "assistant" or sampling_message.content is None:
        return content

    if isinstance(sampling_message.content, TextContent):
        content = sampling_message.content.text
    elif isinstance(sampling_message.content, ImageContent):
        raise ValueError("Image content is not supported for assistant messages.")
    else:
        raise ValueError(f"Unsupported content type: {type(sampling_message.content)}")

    if content is None:
        return None

    return ChatCompletionAssistantMessageParam(
        role="assistant",
        content=content,
    )


def sampling_messages_to_chat_completion_messages(
    sampling_messages: list[SamplingMessage],
) -> list[ChatCompletionMessageParam]:
    """
    Converts a list of SamplingMessages to a list of ChatCompletionMessageParams.
    """

    # FIXME: combine series of same-role messages into one multi-part message
    chat_completion_messages = []
    for sampling_message in sampling_messages:
        match sampling_message.role:
            case "user":
                chat_message = sampling_message_to_chat_completion_user_message(
                    sampling_message
                )
            case "assistant":
                chat_message = sampling_message_to_chat_completion_assistant_message(
                    sampling_message
                )
            case _:
                raise ValueError(f"Unsupported role: {sampling_message.role}")

        if chat_message is not None:
            chat_completion_messages.append(chat_message)

    return chat_completion_messages
