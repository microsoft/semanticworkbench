import logging
from time import perf_counter
from typing import Any, AsyncIterator, Awaitable, Callable, Coroutine, Generic, Iterable, TypeVar

import openai
from attr import dataclass
from openai import NotGiven, pydantic_function_tool
from openai.types.chat import (
    ChatCompletionAssistantMessageParam,
    ChatCompletionMessageParam,
    ChatCompletionMessageToolCallParam,
    ChatCompletionToolChoiceOptionParam,
    ChatCompletionToolMessageParam,
    ParsedFunctionToolCall,
)
from pydantic import BaseModel

from .config import LLMConfig

logger = logging.getLogger(__name__)


TToolArgs = TypeVar("TToolArgs", bound=BaseModel)


@dataclass
class CompletionTool(Generic[TToolArgs]):
    function: Callable[[TToolArgs], Coroutine[Any, Any, str]]
    argument_model: type[TToolArgs]
    description: str = ""
    """Description of the tool. If omitted, wil use the docstring of the function."""


class LLMResponse(BaseModel):
    metadata: dict[str, Any]


class ToolCallResponse(LLMResponse):
    tool_call: ParsedFunctionToolCall
    result: str


class MessageResponse(LLMResponse):
    message: str


class CompletionError(Exception):
    def __init__(self, message: str, metadata: dict[str, Any]) -> None:
        super().__init__(message)
        self.message = message
        self.metadata = metadata

    def __str__(self) -> str:
        return f"CompletionError(message={repr(self.message)}, metadata={repr(self.metadata)})"


async def completion_with_tools(
    llm_config: LLMConfig,
    head_messages: Callable[[], Awaitable[Iterable[ChatCompletionMessageParam]]],
    tail_messages: Callable[[], Awaitable[Iterable[ChatCompletionMessageParam]]],
    tools: list[CompletionTool] = [],
    tool_choice: ChatCompletionToolChoiceOptionParam | None = None,
    ignore_tool_calls_after: int = -1,
    allow_tool_followup: bool = True,
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

    tool_attempts = 0
    async with llm_config.openai_client_factory() as client:
        while tool_attempts <= 2:
            tool_attempts += 1
            completion_messages = list(await head_messages()) + tool_messages + list(await tail_messages())

            metadata = {
                "request": {
                    "model": llm_config.openai_model,
                    "messages": completion_messages,
                    "tools": openai_tools,
                    "reasoning_effort": llm_config.reasoning_effort,
                    "max_completion_tokens": llm_config.max_response_tokens,
                },
            }

            start = perf_counter()
            try:
                response_raw = await client.beta.chat.completions.with_raw_response.parse(
                    messages=completion_messages,
                    model=llm_config.openai_model,
                    tools=openai_tools or NotGiven(),
                    tool_choice=tool_choice or NotGiven(),
                    reasoning_effort=llm_config.reasoning_effort or NotGiven(),
                    max_completion_tokens=llm_config.max_response_tokens,
                    parallel_tool_calls=False if openai_tools else NotGiven(),
                )
            except openai.BadRequestError as e:
                raise CompletionError(
                    message="Failed to parse completion request",
                    metadata={
                        **metadata,
                        "response_duration": perf_counter() - start,
                        "error": str(e),
                    },
                ) from e

            headers = {key: value for key, value in response_raw.headers.items()}
            response = response_raw.parse()

            message = response.choices[0].message

            metadata = {
                **metadata,
                "response": response.model_dump(),
                "response_headers": headers,
                "response_duration": perf_counter() - start,
            }

            if message.content:
                yield MessageResponse(message=str(message.content), metadata=metadata)

            if not message.tool_calls:
                return

            logger.info("tool calls (%d): %s", len(message.tool_calls), message.tool_calls)

            # append the assistant message with the tool calls for the next iteration
            tool_messages.append(
                ChatCompletionAssistantMessageParam(
                    role="assistant",
                    tool_calls=[
                        ChatCompletionMessageToolCallParam(
                            id=tool_call.id,
                            function={
                                "name": tool_call.function.name,
                                "arguments": tool_call.function.arguments,
                            },
                            type="function",
                        )
                        for tool_call in message.tool_calls
                    ],
                )
            )

            for index, tool_call in enumerate(message.tool_calls):
                if ignore_tool_calls_after >= 0 and index > ignore_tool_calls_after:
                    logger.info("ignoring tool call: %s", tool_call)
                    if allow_tool_followup:
                        break
                    return

                function = tool_call.function

                start = perf_counter()
                try:
                    # find the matching tool
                    tool = next((t for t in tools if t.function.__name__ == function.name), None)
                    if tool is None:
                        raise ValueError("Unknown tool call: %s", tool_call.function)

                    # validate the args and call the tool function
                    args = tool.argument_model.model_validate(function.parsed_arguments)
                    result = await tool.function(args)

                    tool_metadata = {
                        **metadata,
                        "tool_call": tool_call.model_dump(mode="json"),
                        "tool_result": result,
                        "tool_duration": perf_counter() - start,
                    }
                    yield ToolCallResponse(tool_call=tool_call, result=result, metadata=tool_metadata)

                    # append the tool result to the messages for the next iteration
                    tool_messages.append(
                        ChatCompletionToolMessageParam(
                            content=result,
                            role="tool",
                            tool_call_id=tool_call.id,
                        )
                    )

                    if not allow_tool_followup:
                        logger.info("skipping completion after tool call")
                        return
                    break

                except Exception as e:
                    logger.warning(
                        "Error calling tool; tool: %s, arguments: %s",
                        tool_call.function.name,
                        tool_call.function.parsed_arguments,
                        exc_info=e,
                    )

                    tool_metadata = {
                        **metadata,
                        "tool_call": tool_call.model_dump(mode="json"),
                        "tool_error": str(e),
                        "tool_duration": perf_counter() - start,
                    }

                    match tool_attempts:
                        case 1:
                            result = f"An error occurred while calling the tool: {e}. Please try again."

                        case _:
                            result = f"An error occurred while calling the tool: {e}. Do not try again. Tell the user what you were trying to do and explain that an error occurred."
                            logger.warning("Fatal error calling tool, exiting tool loop")
                            yield ToolCallResponse(tool_call=tool_call, result=result, metadata=tool_metadata)

                    # append the tool result to the messages for the next iteration
                    tool_messages.append(
                        ChatCompletionToolMessageParam(
                            content=result,
                            role="tool",
                            tool_call_id=tool_call.id,
                        )
                    )

                    # exit the tool loop
                    break
