import logging

from mcp.types import CreateMessageRequestParams, CreateMessageResult
from openai_client import OpenAIRequestConfig, ServiceConfig, create_client

logger = logging.getLogger(__name__)


async def process_sampling_request(
    request: CreateMessageRequestParams,
    service_config: ServiceConfig,
    request_config: OpenAIRequestConfig,
) -> CreateMessageResult:
    """
    Processes a sampling request.
    """

    completion_args = {
        "messages": request.messages,
        "model": request_config.model,
    }

    async with create_client(service_config) as client:
        try:
            completion = await client.chat.completions.create(**completion_args)
        except Exception as e:
            logger.exception(f"exception occurred calling openai chat completion: {e}")
            raise e

    return completion
