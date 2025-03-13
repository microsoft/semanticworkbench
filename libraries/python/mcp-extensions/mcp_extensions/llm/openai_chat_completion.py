# Copyright (c) Microsoft. All rights reserved.

import json
import time
from collections.abc import Callable
from typing import Any, Literal

from azure.identity import DefaultAzureCredential, get_bearer_token_provider
from openai import AzureOpenAI, OpenAI

from mcp_extensions.llm.llm_types import (
    AssistantMessage,
    ChatCompletionChoice,
    ChatCompletionRequest,
    ChatCompletionResponse,
    Function,
    ToolCall,
)


def validate(request: ChatCompletionRequest) -> None:
    if request.json_mode and request.structured_outputs is not None:
        raise ValueError("json_schema and json_mode cannot be used together.")

    # Raise an error if both "max_tokens" and "max_completion_tokens" are provided
    if request.max_tokens is not None and request.max_completion_tokens is not None:
        raise ValueError("`max_tokens` and `max_completion_tokens` cannot both be provided.")


def format_kwargs(request: ChatCompletionRequest) -> dict[str, Any]:
    # Format the response format parameters to be compatible with OpenAI API
    if request.json_mode:
        response_format: dict[str, Any] = {"type": "json_object"}
    elif request.structured_outputs is not None:
        response_format = {"type": "json_schema", "json_schema": request.structured_outputs}
    else:
        response_format = {"type": "text"}

    kwargs = request.model_dump(mode="json", exclude_none=True)

    for message in kwargs["messages"]:
        role = message.get("role", None)
        # For each ToolMessage, change the "name" field to be named "tool_call_id" instead
        if role is not None and role == "tool":
            message["tool_call_id"] = message.pop("name")

        # For each AssistantMessage with tool calls, make the function arguments a string
        if role is not None and role == "assistant" and message.get("tool_calls", None):
            for tool_call in message["tool_calls"]:
                tool_call["function"]["arguments"] = str(tool_call["function"]["arguments"])

    # Delete the json_mode and structured_outputs from kwargs
    kwargs.pop("json_mode", None)
    kwargs.pop("structured_outputs", None)

    # Add the response_format to kwargs
    kwargs["response_format"] = response_format

    # Handle tool_choice when the provided tool_choice the name of the required tool.
    if request.tool_choice is not None and request.tool_choice not in ["none", "auto", "required"]:
        kwargs["tool_choice"] = {"type": "function", "function": {"name": request.tool_choice}}

    return kwargs


def process_logprobs(logprobs_content: list[dict[str, Any]]) -> list[dict[str, Any] | list[dict[str, Any]]]:
    """Process logprobs content from OpenAI API response.

    Args:
        logprobs_content: List of logprob entries from the API response

    Returns:
        Processed logprobs list containing either single token info or lists of top token infos
    """
    logprobs_list: list[dict[str, Any] | list[dict[str, Any]]] = []
    for logprob in logprobs_content:
        if logprob.get("top_logprobs", None):
            curr_logprob_infos: list[dict[str, Any]] = []
            for top_logprob in logprob.get("top_logprobs", []):
                curr_logprob_infos.append({
                    "token": top_logprob.get("token", ""),
                    "logprob": top_logprob.get("logprob", 0),
                    "bytes": top_logprob.get("bytes", 0),
                })
            logprobs_list.append(curr_logprob_infos)
        else:
            logprobs_list.append({
                "token": logprob.get("token", ""),
                "logprob": logprob.get("logprob", 0),
                "bytes": logprob.get("bytes", 0),
            })
    return logprobs_list


def process_response(response: Any, response_duration: float, request: ChatCompletionRequest) -> ChatCompletionResponse:
    errors = ""
    extras: dict[str, Any] = {}
    choices: list[ChatCompletionChoice] = []
    for index, choice in enumerate(response["choices"]):
        choice_extras: dict[str, Any] = {}
        finish_reason = choice["finish_reason"]

        message = choice["message"]
        tool_calls: list[ToolCall] | None = None
        if message.get("tool_calls", None):
            parsed_tool_calls: list[ToolCall] = []
            for tool_call in message["tool_calls"]:
                tool_name = tool_call.get("function", {}).get("name", None)
                # Check if the tool name is valid (one of the tool names in the request)
                if request.tools and tool_name not in [tool["function"]["name"] for tool in request.tools]:
                    errors += f"Choice {index}: Tool call {tool_call} has an invalid tool name: {tool_name}\n"

                tool_args = tool_call.get("function", {}).get("arguments", None)
                try:
                    tool_args = json.loads(tool_args)
                except json.JSONDecodeError:
                    errors += f"Choice {index}: Tool call {tool_call} failed to parse arguments into JSON\n"

                parsed_tool_calls.append(
                    ToolCall(
                        id=tool_call["id"],
                        function=Function(
                            name=tool_name,
                            arguments=tool_args,
                        ),
                    )
                )
            tool_calls = parsed_tool_calls

        json_message = None
        if request.json_mode or (request.structured_outputs is not None):
            try:
                json_message = json.loads(message.get("content", "{}"))
            except json.JSONDecodeError:
                errors += f"Choice {index}: Message failed to parse into JSON\n"

        # Handle logprobs
        logprobs: list[dict[str, Any] | list[dict[str, Any]]] | None = None
        if choice.get("logprobs", None) and choice["logprobs"].get("content", None) is not None:
            logprobs = process_logprobs(choice["logprobs"]["content"])

        # Handle extras that OpenAI or Azure OpenAI return
        if choice.get("content_filter_results", None):
            choice_extras["content_filter_results"] = choice["content_filter_results"]

        choices.append(
            ChatCompletionChoice(
                message=AssistantMessage(
                    content=message.get("content") or "",
                    refusal=message.get("refusal", None),
                    tool_calls=tool_calls,
                ),
                finish_reason=finish_reason,
                json_message=json_message,
                logprobs=logprobs,
                extras=choice_extras,
            )
        )

    completion_tokens = response["usage"].get("completion_tokens", -1)
    prompt_tokens = response["usage"].get("prompt_tokens", -1)
    completion_detailed_tokens = response["usage"].get("completion_detailed_tokens", None)
    prompt_detailed_tokens = response["usage"].get("prompt_detailed_tokens", None)
    system_fingerprint = response.get("system_fingerprint", None)

    extras["prompt_filter_results"] = response.get("prompt_filter_results", None)

    return ChatCompletionResponse(
        choices=choices,
        errors=errors.strip(),
        extras=extras,
        completion_tokens=completion_tokens,
        prompt_tokens=prompt_tokens,
        completion_detailed_tokens=completion_detailed_tokens,
        prompt_detailed_tokens=prompt_detailed_tokens,
        system_fingerprint=system_fingerprint,
        response_duration=response_duration,
    )


def openai_chat_completion(request: ChatCompletionRequest, client: Callable[..., Any]) -> ChatCompletionResponse:
    validate(request)
    kwargs = format_kwargs(request)

    start_time = time.time()
    response = client(**kwargs)
    end_time = time.time()
    response_duration = round(end_time - start_time, 4)

    processed_response = process_response(response, response_duration, request)
    return processed_response


def create_client_callable(client_class: type[OpenAI | AzureOpenAI], **client_args: Any) -> Callable[..., Any]:
    """Creates a callable that instantiates and uses an OpenAI client.

    Args:
        client_class: The OpenAI client class to instantiate (OpenAI or AzureOpenAI)
        **client_args: Arguments to pass to the client constructor

    Returns:
        A callable that creates a client and returns completion results
    """
    filtered_args = {k: v for k, v in client_args.items() if v is not None}

    def client_callable(**kwargs: Any) -> Any:
        client = client_class(**filtered_args)
        completion = client.chat.completions.create(**kwargs)
        return completion.to_dict()

    return client_callable


class InvalidOAIAPITypeError(Exception):
    """Raised when an invalid OAIAPIType string is provided."""


def openai_client(
    api_type: Literal["openai", "azure_openai"] = "openai",
    api_key: str | None = None,
    organization: str | None = None,
    aoai_api_version: str = "2024-06-01",
    azure_endpoint: str | None = None,
    timeout: float | None = None,
    max_retries: int | None = None,
) -> Callable[..., Any]:
    """Create an OpenAI or Azure OpenAI client instance based on the specified API type and other provided parameters.

    It is preferred to use RBAC authentication for Azure OpenAI. You must be signed in with the Azure CLI and have correct role assigned.
    See https://techcommunity.microsoft.com/t5/microsoft-developer-community/using-keyless-authentication-with-azure-openai/ba-p/4111521

    Args:
        api_type (str, optional): Type of the API to be used. Accepted values are 'openai' or 'azure_openai'.
            Defaults to 'openai'.
        api_key (str, optional): The API key to authenticate the client. If not provided,
            OpenAI automatically uses `OPENAI_API_KEY` from the environment.
            If provided for Azure OpenAI, it will be used for authentication instead of the Azure AD token provider.
        organization (str, optional): The ID of the organization. If not provided,
            OpenAI automatically uses `OPENAI_ORG_ID` from the environment.
        aoai_api_version (str, optional): Only applicable if using Azure OpenAI https://learn.microsoft.com/azure/ai-services/openai/reference#rest-api-versioning
        azure_endpoint (str, optional): The endpoint to use for Azure OpenAI.
        timeout (float, optional): By default requests time out after 10 minutes.
        max_retries (int, optional): Certain errors are automatically retried 2 times by default,
            with a short exponential backoff. Connection errors (for example, due to a network connectivity problem),
            408 Request Timeout, 409 Conflict, 429 Rate Limit, and >=500 Internal errors are all retried by default.

    Returns:
        Callable[..., Any]: A callable that creates a client and returns completion results

    Raises:
        InvalidOAIAPITypeError: If an invalid API type string is provided.
        NotImplementedError: If the specified API type is recognized but not yet supported (e.g., 'azure_openai').
    """
    if api_type not in ["openai", "azure_openai"]:
        raise InvalidOAIAPITypeError(f"Invalid OAIAPIType: {api_type}. Must be 'openai' or 'azure_openai'.")

    if api_type == "openai":
        return create_client_callable(
            OpenAI,  # type: ignore
            api_key=api_key,
            organization=organization,
            timeout=timeout,
            max_retries=max_retries,
        )
    elif api_type == "azure_openai":
        if api_key:
            return create_client_callable(
                AzureOpenAI,
                api_version=aoai_api_version,
                azure_endpoint=azure_endpoint,
                api_key=api_key,
                timeout=timeout,
                max_retries=max_retries,
            )
        else:
            azure_credential = DefaultAzureCredential()
            ad_token_provider = get_bearer_token_provider(
                azure_credential, "https://cognitiveservices.azure.com/.default"
            )
            return create_client_callable(
                AzureOpenAI,
                api_version=aoai_api_version,
                azure_endpoint=azure_endpoint,
                azure_ad_token_provider=ad_token_provider,
                timeout=timeout,
                max_retries=max_retries,
            )
    else:
        raise NotImplementedError(f"API type '{api_type}' is invalid.")
