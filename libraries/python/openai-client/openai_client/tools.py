import json
from typing import Any, Iterable

from function_registry import FunctionRegistry
from openai import (
    AsyncAzureOpenAI,
    AsyncOpenAI,
    NotGiven,
)
from openai.types.chat import (
    ChatCompletionMessageParam,
    ChatCompletionToolParam,
    ParsedChatCompletion,
    ParsedFunctionToolCall,
)

from . import logger
from .completion import assistant_message_from_completion
from .errors import CompletionError, validate_completion
from .logging import extra_data, serializable_completion_args


async def execute_tool_call(
    tool_call: ParsedFunctionToolCall,
    function_registry: FunctionRegistry,
) -> ChatCompletionMessageParam | None:
    """
    Execute a tool call function using a Function Registry and return the response as a message.
    """
    function = tool_call.function
    if function_registry.has_function(function.name):
        logger.debug(
            "Function call.",
            extra=extra_data({"name": function.name, "arguments": function.arguments}),
        )
        try:
            kwargs: dict[str, Any] = json.loads(function.arguments)
            value = await function_registry.execute_function_with_string_response(function.name, (), kwargs)
        except Exception as e:
            logger.error("Error.", extra=extra_data({"error": e}))
            value = f"Error: {e}"
        finally:
            logger.debug("Function response.", extra=extra_data({"tool_call_id": tool_call.id, "content": value}))
            return {
                "role": "tool",
                "content": value,
                "tool_call_id": tool_call.id,
            }
    else:
        logger.error(f"Function not found: {function.name}")


def function_registry_to_tools(function_registry: FunctionRegistry) -> Iterable[ChatCompletionToolParam] | NotGiven:
    # Only the "functions" tool is available in the Chat API.
    # https://platform.openai.com/docs/guides/function-calling

    # If the only tool is the default function registry help function, then
    # we don't want to tell the chat response that we have any tools.
    if function_registry.list_functions() == ["help"]:
        return NotGiven()

    return [
        ChatCompletionToolParam(**{
            "type": "function",
            "function": func.schema,
        })
        for func in function_registry.get_functions()
    ]


def tool_choice(functions: list[str] | None) -> Iterable[ChatCompletionToolParam] | None:
    if not functions:
        return None
    return [
        ChatCompletionToolParam(**{
            "type": "function",
            "function": {"name": name},
        })
        for name in functions
    ] or None


async def complete_with_tool_calls(
    async_client: AsyncOpenAI | AsyncAzureOpenAI,
    function_registry: FunctionRegistry,
    completion_args: dict[str, Any],
    metadata: dict[str, Any] = {},
) -> tuple[ParsedChatCompletion | None, list[ChatCompletionMessageParam]]:
    """
    Complete a chat response with tool calls handled by Function Registry-registered functions.

    Parameters:
    - async_client: The OpenAI client.
    - function_registry: The function registry.
    - completion_args: The completion arguments wassed onto the OpenAI `parse` call. See the OpenAI API docs for more information.
    - metadata: Metadata to be added to the completion response.
    """
    # Pull out a reference to the completion args messages.
    messages: list[ChatCompletionMessageParam] = completion_args.get("messages", [])
    new_messages: list[ChatCompletionMessageParam] = []

    # Completion call.
    logger.debug("Completion call.", extra=extra_data(serializable_completion_args(completion_args)))
    metadata["completion_args"] = serializable_completion_args(completion_args)
    try:
        completion = await async_client.beta.chat.completions.parse(
            **completion_args,
        )
        validate_completion(completion)
        logger.debug("Completion response.", extra=extra_data({"completion": completion.model_dump()}))
        metadata["completion"] = completion.model_dump()
    except CompletionError as e:
        completion_error = CompletionError(e)
        metadata["completion_error"] = completion_error.message
        logger.error(e.message, extra=extra_data({"completion_error": completion_error.body, "metadata": metadata}))
        raise completion_error from e

    # Extract response and add to messages.
    assistant_message = assistant_message_from_completion(completion)
    if assistant_message:
        new_messages.append(assistant_message)

    # If no tool calls, we're done.
    completion_message = completion.choices[0].message
    if not completion_message.tool_calls:
        return completion, new_messages

    # Call all tool functions and generate return messages.
    for tool_call in completion_message.tool_calls:
        function_call_result_message = await execute_tool_call(tool_call, function_registry)
        if function_call_result_message:
            new_messages.append(function_call_result_message)

    # Completion call for final response.
    final_args = {**completion_args, "messages": [*messages, *new_messages]}
    del final_args["tools"]
    del final_args["tool_choice"]
    logger.debug("Tool completion call.", extra=extra_data(serializable_completion_args(final_args)))
    metadata["tool_completion_args"] = serializable_completion_args(final_args)
    try:
        tool_completion = await async_client.beta.chat.completions.parse(
            **final_args,
        )
        validate_completion(tool_completion)
        logger.debug("Tool completion response.", extra=extra_data({"completion": completion.model_dump()}))
        metadata["completion"] = completion.model_dump()
    except Exception as e:
        tool_completion_error = CompletionError(e)
        metadata["tool_completion_error"] = tool_completion_error.message
        logger.error(
            tool_completion_error.message,
            extra=extra_data({"completion_error": tool_completion_error.body, "metadata": metadata}),
        )
        raise tool_completion_error from e

    # Add assistant response to messages.
    tool_completion_assistant_message = assistant_message_from_completion(tool_completion)
    if tool_completion_assistant_message:
        new_messages.append(tool_completion_assistant_message)

    return tool_completion, new_messages
