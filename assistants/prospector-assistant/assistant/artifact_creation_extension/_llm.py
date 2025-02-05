import logging
from abc import ABC, abstractmethod
from typing import Any, AsyncIterator, Awaitable, Callable, Coroutine, Generic, Iterable, TypeVar

from attr import dataclass
from openai import pydantic_function_tool
from openai.types.chat import (
    ChatCompletionAssistantMessageParam,
    ChatCompletionMessageParam,
    ChatCompletionMessageToolCallParam,
    ChatCompletionToolMessageParam,
    ParsedFunctionToolCall,
)
from pydantic import BaseModel
from semantic_workbench_assistant.assistant_app.context import ConversationContext

from .config import LLMConfig

logger = logging.getLogger(__name__)


class NoResponseChoicesError(Exception):
    pass


class NoParsedMessageError(Exception):
    pass


ResponseModelT = TypeVar("ResponseModelT", bound=BaseModel)


async def structured_completion(
    llm_config: LLMConfig, messages: list[ChatCompletionMessageParam], response_model: type[ResponseModelT]
) -> tuple[ResponseModelT, dict[str, Any]]:
    async with llm_config.openai_client_factory() as client:
        response = await client.beta.chat.completions.parse(
            messages=messages,
            model=llm_config.openai_model,
            response_format=response_model,
            max_tokens=llm_config.max_response_tokens,
        )

        if not response.choices:
            raise NoResponseChoicesError()

        if not response.choices[0].message.parsed:
            raise NoParsedMessageError()

        metadata = {
            "request": {
                "model": llm_config.openai_model,
                "messages": messages,
                "max_tokens": llm_config.max_response_tokens,
                "response_format": response_model.model_json_schema(),
            },
            "response": response.model_dump(),
        }

        return response.choices[0].message.parsed, metadata


class ToolArgsModel(ABC, BaseModel):
    @abstractmethod
    def set_context(self, context: ConversationContext) -> None: ...


TToolArgs = TypeVar("TToolArgs", bound=ToolArgsModel)
TToolResult = TypeVar("TToolResult", bound=BaseModel)


@dataclass
class CompletionTool(Generic[TToolArgs, TToolResult]):
    function: Callable[[TToolArgs], Coroutine[Any, Any, TToolResult]]
    argument_model: type[TToolArgs]
    description: str = ""
    """Description of the tool. If omitted, wil use the docstring of the function."""


@dataclass
class LLMResponse:
    metadata: dict[str, Any]


@dataclass
class ToolCallResponse(LLMResponse):
    tool_call: ParsedFunctionToolCall
    result: BaseModel


@dataclass
class MessageResponse(LLMResponse):
    message: str


async def completion_with_tools(
    llm_config: LLMConfig,
    context: ConversationContext,
    get_messages: Callable[[], Awaitable[Iterable[ChatCompletionMessageParam]]],
    tools: list[CompletionTool] = [],
) -> AsyncIterator[ToolCallResponse | MessageResponse]:
    openai_tools = [
        pydantic_function_tool(
            tool.argument_model,
            name=tool.function.__name__,
            description=tool.description or (tool.function.__doc__ or "").strip(),
        )
        for tool in tools
    ]

    tool_messages: list[ChatCompletionMessageParam] = []
    reasoning_effort = "medium"

    async with llm_config.openai_client_factory() as client:
        while True:
            completion_messages = list(await get_messages()) + tool_messages

            response = await client.beta.chat.completions.parse(
                messages=completion_messages,
                model=llm_config.openai_model,
                max_completion_tokens=llm_config.max_response_tokens + 25_000,
                tools=openai_tools,
                reasoning_effort=reasoning_effort,
                # parallel_tool_calls=False,
            )

            message = response.choices[0].message

            if not message.tool_calls:
                metadata = {
                    "request": {
                        "model": llm_config.openai_model,
                        "messages": completion_messages,
                        "tools": openai_tools,
                        "reasoning_effort": reasoning_effort,
                        "max_completion_tokens": llm_config.max_response_tokens,
                    },
                    "response": response.model_dump(),
                }
                yield MessageResponse(message=str(message.content), metadata=metadata)
                return

            async with context.set_status("calling tools..."):
                logger.info("tool calls: %s", message.tool_calls)

                # append the assistant message with the tool calls for the next iteration
                tool_messages.append(
                    ChatCompletionAssistantMessageParam(
                        role="assistant",
                        tool_calls=[
                            ChatCompletionMessageToolCallParam(
                                id=c.id,
                                function={
                                    "name": c.function.name,
                                    "arguments": c.function.arguments,
                                },
                                type="function",
                            )
                            for c in message.tool_calls
                        ],
                    )
                )
                for tool_call in message.tool_calls:
                    function = tool_call.function

                    # find the matching tool
                    tool = next((t for t in tools if t.function.__name__ == function.name), None)
                    if tool is None:
                        raise ValueError("Unknown tool call: %s", tool_call.function)

                    # validate the args and call the tool function
                    args = tool.argument_model.model_validate(function.parsed_arguments)
                    args.set_context(context)
                    result: BaseModel = await tool.function(args)

                    metadata = {
                        "request": {
                            "model": llm_config.openai_model,
                            "messages": completion_messages,
                            "tools": openai_tools,
                            "max_tokens": llm_config.max_response_tokens,
                        },
                        "response": response.model_dump(),
                        "tool_call": tool_call.model_dump(mode="json"),
                        "tool_result": result.model_dump(mode="json"),
                    }
                    yield ToolCallResponse(tool_call=tool_call, result=result, metadata=metadata)

                    # append the tool result to the messages for the next iteration
                    tool_messages.append(
                        ChatCompletionToolMessageParam(
                            content=result.model_dump_json(),
                            role="tool",
                            tool_call_id=tool_call.id,
                        )
                    )
