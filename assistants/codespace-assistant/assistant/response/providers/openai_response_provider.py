# Copyright (c) Microsoft. All rights reserved.

import json
import logging
from textwrap import dedent
from typing import Any, List, Sequence, Tuple, Type

import deepmerge
import openai_client
from assistant_extensions.ai_clients.config import AzureOpenAIClientConfigModel, OpenAIClientConfigModel
from assistant_extensions.ai_clients.model import CompletionMessage
from mcp import Tool
from openai import AsyncOpenAI, NotGiven
from openai.types.chat import (
    ChatCompletion,
    ChatCompletionMessageParam,
    ChatCompletionToolParam,
    ParsedChatCompletion,
)
from openai.types.shared_params import FunctionDefinition
from pydantic import BaseModel
from semantic_workbench_api_model.workbench_model import (
    MessageType,
)
from semantic_workbench_assistant.assistant_app import (
    ConversationContext,
)

from ...config import AssistantConfigModel
from ...extensions.tools.__model import ToolsConfigModel
from .base_provider import NumberTokensResult, ResponseProvider, ResponseResult, ToolAction

logger = logging.getLogger(__name__)


class OpenAIToolCallStructuredOutput(BaseModel):
    class Config:
        extra = "forbid"
        json_schema_extra = {
            "description": (
                "The format for a tool call. Only use the provided tool definitions to define the tool calls."
            ),
            "required": ["id", "function"],
        }

    id: str
    function: str
    arguments: dict


class StructuredResponse(BaseModel):
    class Config:
        extra = "forbid"
        json_schema_extra = {
            "description": (
                "The response format for the assistant. Use the assistant_response field for the"
                " response content and the tool_calls field for any tool calls. Use the assistant_response"
                " to inform the user of what you are doing as they will see this status while the tool"
                " calls run."
            ),
            "required": ["assistant_response", "tool_calls"],
        }

    assistant_response: str
    tool_calls: List[OpenAIToolCallStructuredOutput]


class OpenAIResponseProvider(ResponseProvider):
    def __init__(
        self,
        conversation_context: ConversationContext,
        assistant_config: AssistantConfigModel,
        openai_client_config: OpenAIClientConfigModel | AzureOpenAIClientConfigModel,
    ) -> None:
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

    async def get_generative_response(
        self,
        messages: List[CompletionMessage],
        metadata_key: str,
        mcp_tools: List[Tool] | None,
    ) -> ResponseResult:
        response_result = ResponseResult(
            content=None,
            tool_actions=None,
            message_type=MessageType.chat,
            metadata={},
            completion_total_tokens=0,
        )

        # define the metadata key for any metadata created within this method
        method_metadata_key = f"{metadata_key}:openai"

        # initialize variables for the response content
        completion: ParsedChatCompletion | ChatCompletion | None = None

        # convert the messages to chat completion message parameters
        chat_message_params: List[ChatCompletionMessageParam] = openai_client.convert_from_completion_messages(messages)

        # convert the tools to make them compatible with the OpenAI API
        tools = convert_mcp_tools_to_openai_tools(mcp_tools)

        # generate a response from the AI model
        async with openai_client.create_client(self.service_config) as client:
            try:
                completion = await self.get_completion(client, self.request_config, chat_message_params, tools)

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

            response_content: list[str] = []

            if (completion.choices[0].message.content is not None) and (
                completion.choices[0].message.content.strip() != ""
            ):
                response_content.append(completion.choices[0].message.content)

            # check if the completion has tool calls
            if completion.choices[0].message.tool_calls:
                ai_context, tool_actions = extract_content_from_tool_actions([
                    ToolAction(
                        id=tool_call.id,
                        name=tool_call.function.name,
                        arguments=json.loads(
                            tool_call.function.arguments,
                        ),
                    )
                    for tool_call in completion.choices[0].message.tool_calls
                ])
                response_result.tool_actions = tool_actions
                if ai_context is not None and ai_context.strip() != "":
                    response_content.append(ai_context)

            response_result.content = "\n\n".join(response_content)

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
                            "tools": tools,
                        },
                        "response": completion.model_dump() if completion else "[no response from openai]",
                    },
                },
            },
        )

        # send the response to the conversation
        return response_result

    async def get_response(
        self,
        messages: List[CompletionMessage],
        metadata_key: str,
        tools_extension_config: ToolsConfigModel,
        mcp_tools: List[Tool] | None,
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
            tool_actions=None,
            message_type=MessageType.chat,
            metadata={},
            completion_total_tokens=0,
        )

        # define the metadata key for any metadata created within this method
        method_metadata_key = f"{metadata_key}:openai"

        # initialize variables for the response content
        completion: ParsedChatCompletion | ChatCompletion | None = None

        # convert the messages to chat completion message parameters
        chat_message_params: List[ChatCompletionMessageParam] = openai_client.convert_from_completion_messages(messages)

        # convert the tools to make them compatible with the OpenAI API
        tools = convert_mcp_tools_to_openai_tools(mcp_tools)

        if self.request_config.is_reasoning_model:
            chat_message_params = customize_chat_message_params_for_reasoning(
                chat_message_params, tools_extension_config, tools
            )

        # generate a response from the AI model
        async with openai_client.create_client(self.service_config) as client:
            try:
                if self.request_config.model == "o1-preview":
                    # o1-preview does not support tools calls, so we need to hack around that

                    # make a normal completion
                    first_completion = await self.get_completion(
                        client, self.request_config, chat_message_params, tools
                    )

                    first_completion_content = first_completion.choices[0].message.content

                    # if the message content has tools_calls content, pass to fallback model
                    # to have it transform it to structured output
                    if (
                        tools is not None
                        and first_completion_content is not None
                        # FIXME: quick hack to test
                        and "assistant_response" in first_completion_content
                        and "tool_calls" in first_completion_content
                    ):
                        # FIXME: Disabled for now, will instead implement multi-model support
                        # use the fallback model to transform the content to a tools call
                        # completion = await self.use_fallback_model_to_transform_tool_calls(
                        #     config,
                        #     first_completion_content,
                        #     tools,
                        # )

                        raise NotImplementedError("o1-preview does not support tool calls")

                    else:
                        # no tool calls, so we can use the completion as is
                        completion = first_completion

                else:
                    completion = await self.get_completion(client, self.request_config, chat_message_params, tools)

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

            response_content: list[str] = []

            if (completion.choices[0].message.content is not None) and (
                completion.choices[0].message.content.strip() != ""
            ):
                response_content.append(completion.choices[0].message.content)

            # check if the completion has tool calls
            if completion.choices[0].message.tool_calls:
                ai_context, tool_actions = extract_content_from_tool_actions([
                    ToolAction(
                        id=tool_call.id,
                        name=tool_call.function.name,
                        arguments=json.loads(
                            tool_call.function.arguments,
                        ),
                    )
                    for tool_call in completion.choices[0].message.tool_calls
                ])
                response_result.tool_actions = tool_actions
                if ai_context is not None and ai_context.strip() != "":
                    response_content.append(ai_context)

            response_result.content = "\n\n".join(response_content)

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

    async def get_completion(
        self,
        client: AsyncOpenAI,
        request_config: openai_client.OpenAIRequestConfig,
        chat_message_params: List[ChatCompletionMessageParam],
        tools: List[ChatCompletionToolParam] | None,
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
            # note: tools are not supported by reasoning models currently
            completion_args["max_completion_tokens"] = request_config.response_tokens

        else:
            # all other models
            completion_args["max_tokens"] = request_config.response_tokens
            completion_args["tools"] = tools or NotGiven()
            if tools is not None:
                completion_args["tool_choice"] = "auto"

        return await client.chat.completions.create(**completion_args)

    async def get_parsed_completion(
        self,
        client: AsyncOpenAI,
        request_config: openai_client.OpenAIRequestConfig,
        chat_message_params: List[ChatCompletionMessageParam],
        response_format: Type[BaseModel],
    ) -> ParsedChatCompletion[BaseModel]:
        """
        Generate a parsed completion from the OpenAI API.
        """

        completion_args = {
            "messages": chat_message_params,
            "model": request_config.model,
            "response_format": response_format,
        }

        if request_config.is_reasoning_model:
            # reasoning models
            completion_args["max_completion_tokens"] = request_config.response_tokens

        else:
            # all other models
            completion_args["max_tokens"] = request_config.response_tokens

        return await client.beta.chat.completions.parse(**completion_args)

    # async def use_fallback_model_to_transform_tool_calls(
    #     self,
    #     config: AssistantConfigModel,
    #     content: str,
    #     tools: List[ChatCompletionToolParam],
    # ) -> ChatCompletion:
    #     # use the fallback model to transform the content to a tools call
    #     fallback_service_config = get_fallback_service_config(self.service_config)
    #     fallback_request_config = get_fallback_request_config(self.request_config)

    #     async with openai_client.create_client(fallback_service_config) as fallback_client:
    #         # make the fallback completion

    #         chat_message_params: List[ChatCompletionMessageParam] = [
    #             ChatCompletionUserMessageParam(role="user", content=f"Please make the following tool call: {content}"),
    #         ]

    #         completion = await self.get_completion(fallback_client, fallback_request_config, chat_message_params, tools)

    #         return completion


def customize_chat_message_params_for_reasoning(
    chat_message_params: List[ChatCompletionMessageParam],
    tools_extension_config: ToolsConfigModel,
    tools: List[ChatCompletionToolParam] | None,
) -> List[ChatCompletionMessageParam]:
    """
    Applies some hacks to the chat completions to make them work with reasoning models.
    """

    # reasoning models do not support tool calls, so we will hack it via instruction
    if tools is not None:
        chat_message_params = inject_tools_into_system_message(chat_message_params, tools_extension_config, tools)

    # convert all messages that use system role to user role as reasoning models do not
    # support system role - at all, not even the first message/instruction
    chat_message_params = [
        {
            "role": "user",
            "content": message["content"],
        }
        if message["role"] == "system"
        else message
        for message in chat_message_params
    ]

    return chat_message_params


def extract_content_from_tool_actions(
    tool_actions: List[ToolAction],
) -> Tuple[str | None, List[ToolAction]]:
    """
    Extracts the AI content from the tool actions.

    This function takes a list of ToolAction objects and extracts the AI content from them. It returns a tuple
    containing the AI content and the updated list of ToolAction objects.

    Args:
        tool_actions (List[ToolAction]): The list of ToolAction objects.

    Returns:
        Tuple[str | None, List[ToolAction]]: A tuple containing the AI content and the updated list of ToolAction
        objects.
    """
    ai_content: list[str] = []
    updated_tool_actions = []

    for tool_action in tool_actions:
        # Split the AI content from the tool action
        content, updated_tool_action = split_ai_content_from_tool_action(tool_action)

        if content is not None:
            # FIXME: let's try without showing the tool call, to prevent hallucinated calls in responses
            ai_content.append(content)
            # ai_content += f"{content}\n```tool_call\n{tool_action.name}\n{tool_action.arguments}\n```\n\n"

        updated_tool_actions.append(updated_tool_action)

    return "\n\n".join(ai_content).strip(), updated_tool_actions


def split_ai_content_from_tool_action(
    tool_action: ToolAction,
) -> Tuple[str | None, ToolAction]:
    """
    Splits the AI content from the tool action.
    """

    # Check if the tool action has an "aiContext" argument
    if "aiContext" in tool_action.arguments:
        # Extract the AI content
        ai_content = tool_action.arguments.pop("aiContext")

        # Return the AI content and the updated tool action
        return ai_content, tool_action

    return None, tool_action


def convert_mcp_tools_to_openai_tools(mcp_tools: List[Tool] | None) -> List[ChatCompletionToolParam] | None:
    if not mcp_tools:
        return None

    tools_list: List[ChatCompletionToolParam] = []
    for mcp_tool in mcp_tools:
        # add parameter for explaining the step for the user observing the assistant
        aiContext: dict[str, Any] = {
            "type": "string",
            "description": (
                "Explanation of why the AI is using this tool and what it expects to accomplish."
                "This message is displayed to the user, coming from the point of view of the assistant"
                " and should fit within the flow of the ongoing conversation, responding to the"
                " preceding user message."
            ),
        }

        tools_list.append(
            ChatCompletionToolParam(
                function=FunctionDefinition(
                    name=mcp_tool.name,
                    description=mcp_tool.description if mcp_tool.description else "[no description provided]",
                    parameters=deepmerge.always_merger.merge(
                        mcp_tool.inputSchema,
                        {
                            "properties": {
                                "aiContext": aiContext,
                            },
                        },
                    ),
                ),
                type="function",
            )
        )
    return tools_list


def inject_tools_into_system_message(
    chat_message_params: List[ChatCompletionMessageParam],
    tools_extension_config: ToolsConfigModel,
    tools: List[ChatCompletionToolParam],
) -> List[ChatCompletionMessageParam]:
    """
    Inject tools into the system message.

    This function takes a list of chat message parameters and a list of tools, and injects the tools into the
    system message. The system message is updated to include the tool descriptions and instructions for using
    the tools.

    Args:
        chat_message_params (List[ChatCompletionMessageParam]): The list of chat message parameters.
        tools (List[ChatCompletionToolParam]): The list of tools.

    Returns:
        List[ChatCompletionMessageParam]: The updated list of chat message parameters with the tools injected.
    """
    # assume the first message is the system message
    # TODO: decide if we need something more robust here
    first_system_message_index = 0

    # get the system message
    first_system_message_content = chat_message_params[first_system_message_index].get("content", "")

    # append the tools list and descriptions to the system message
    tools_prompt = create_tools_instructions(tools_extension_config, tools)

    # update the system message content to include the tools prompt
    chat_message_params[first_system_message_index]["content"] = f"{first_system_message_content}\n\n{tools_prompt}"

    return chat_message_params


def create_tools_instructions(tools_extension_config: ToolsConfigModel, tools: List[ChatCompletionToolParam]) -> str:
    tool_definitions = ""
    for tool in tools:
        function: FunctionDefinition = tool.get("function")
        tool_definitions += (
            f"Tool Name: {function.get('name')}\n"
            f"Description: {function.get('description')}\n"
            f"Input Parameters: {json.dumps(function.get('parameters'))}\n\n"
        )

    return openai_client.format_with_liquid(
        tools_extension_config.tools_instructions,
        {
            "tools": dedent(f"""
                {tool_definitions}
                Response format:
                {StructuredResponse.model_json_schema()}
            """)
        },
    )


# def get_fallback_service_config(
#     service_config: openai_client.AzureOpenAIServiceConfig | openai_client.OpenAIServiceConfig,
# ) -> openai_client.AzureOpenAIServiceConfig | openai_client.OpenAIServiceConfig:
#     """
#     Get the fallback service config.

#     This function takes a service config and returns a copy of it with the fallback deployment set.
#     """
#     # make a copy for service_config to new fallback_service_config
#     fallback_service_config: openai_client.AzureOpenAIServiceConfig | openai_client.OpenAIServiceConfig = (
#         service_config.model_copy(deep=True)
#     )

#     # if using Azure OpenAI, swap the deployment for the fallback one
#     if isinstance(fallback_service_config, openai_client.AzureOpenAIServiceConfig):
#         fallback_deployment = fallback_service_config.azure_openai_fallback_deployment
#         if fallback_deployment.strip() == "":
#             raise ValueError("Fallback deployment not set for Azure OpenAI config.")
#         fallback_service_config.azure_openai_deployment = fallback_deployment

#     return fallback_service_config


# def get_fallback_request_config(
#     request_config: openai_client.OpenAIRequestConfig,
# ) -> openai_client.OpenAIRequestConfig:
#     """
#     Get the fallback request config.

#     This function takes a request config and returns a copy of it with the fallback model set.
#     """
#     fallback_request_config = request_config.model_copy(deep=True)
#     fallback_model = request_config.fallback_model
#     if fallback_model.strip() == "":
#         raise ValueError("Fallback model not set for OpenAI config.")
#     fallback_request_config.model = fallback_model

#     # set the response tokens to a reasonable value for the fallback model
#     fallback_request_config.response_tokens = 16_384

#     # set the reasoning model flag to False
#     fallback_request_config.is_reasoning_model = False

#     return fallback_request_config
