import logging
from typing import Any

from mcp import ClientSession, CreateMessageResult
from mcp.shared.context import RequestContext
from mcp.types import CreateMessageRequestParams, ErrorData, TextContent
from openai.types.chat import ChatCompletion, ChatCompletionToolParam
from openai_client import OpenAIRequestConfig, ServiceConfig, create_client

logger = logging.getLogger(__name__)


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

        completion_args = {
            "messages": request.messages,
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
