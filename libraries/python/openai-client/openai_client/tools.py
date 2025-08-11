import ast
import inspect
import json
from collections.abc import Callable, Iterable
from dataclasses import dataclass
from typing import Any

from openai import (
    NOT_GIVEN,
    AsyncOpenAI,
    NotGiven,
)
from openai.types.chat import (
    ChatCompletionMessageParam,
    ChatCompletionToolParam,
    ParsedChatCompletion,
    ParsedFunctionToolCall,
)
from openai.types.shared_params.function_definition import FunctionDefinition
from pydantic import BaseModel, create_model
from pydantic.fields import FieldInfo

from . import logger
from .completion import assistant_message_from_completion
from .errors import CompletionError, validate_completion
from .logging import (
    add_serializable_data,
    make_completion_args_serializable,
    serializable,
)


def to_string(value: Any) -> str:
    """
    Convert a value to a string. This is a helper function to get the response
    of a tool function call into a message.
    """
    if value is None:
        return "Function executed successfully."
    elif isinstance(value, str):
        return value
    elif isinstance(value, int | float):
        return str(value)
    elif isinstance(value, dict):
        return json.dumps(value)
    elif isinstance(value, list):
        return json.dumps(value, indent=2)
    elif isinstance(value, tuple):
        return json.dumps(value)
    elif isinstance(value, BaseModel):
        return value.model_dump_json(indent=2)
    else:
        return str(value)


def function_list_to_tool_choice(
    functions: list[str] | None,
) -> Iterable[ChatCompletionToolParam] | None:
    """
    Convert a list of function names to a list of ChatCompletionToolParam
    objects. This is used in the Chat Completions API if you want to tell the
    completion it MUST use a specific set of tool functions.
    """
    if not functions:
        return None
    return [
        ChatCompletionToolParam(type="function", function={"name": name})
        for name in functions
    ] or None


@dataclass
class Parameter:
    """
    Tool functions are described by their parameters. This dataclass
    describes a single parameter of a tool function.
    """

    name: str
    type: Any
    description: str | None
    default_value: Any | None = None


class ToolFunction:
    """
    A tool function is a Python function that can be called as a tool from the
    chat completion API. This class wraps a function so you can generate it's
    JSON schema for the chat completion API, execute it with arguments, and
    generate a usage string (for help messages)
    """

    def __init__(
        self, fn: Callable, name: str | None = None, description: str | None = None
    ) -> None:
        self.fn = fn
        self.name = name or fn.__name__
        self.description = (
            description or inspect.getdoc(fn) or self.name.replace("_", " ").title()
        )

    def parameters(self, exclude: list[str] | None = None) -> list[Parameter]:
        """
        This function's parameters and their default values.
        """
        if exclude is None:
            exclude = []
        parameters = dict(inspect.signature(self.fn).parameters)
        for param_name in exclude:
            del parameters[param_name]
        return [
            Parameter(
                name=param_name,
                type=param.annotation,
                description=None,  # param.annotation.description,
                default_value=param.default,
            )
            for param_name, param in parameters.items()
        ]

    def usage(self) -> str:
        """
        A usage string for this function. This can be used in help messages.
        """
        name = self.name
        param_usages = []
        for param in self.parameters():
            param_type = param.type
            try:
                param_type = param.type.__name__
            except AttributeError:
                param_type = param.type
            usage = f"{param.name}: {param_type}"
            if param.default_value is not inspect.Parameter.empty:
                if isinstance(param.default_value, str):
                    usage += f' = "{param.default_value}"'
                else:
                    usage += f" = {param.default_value}"
            param_usages.append(usage)

        description = self.description
        return f"{name}({', '.join(param_usages)}): {description}"

    def schema(self, strict: bool = True) -> dict[str, Any]:
        """
        Generate a JSON schema for this function that is suitable for the OpenAI
        completion API.
        """

        # Create the Pydantic model using create_model.
        model_name = self.fn.__name__.title().replace("_", "")
        fields = {}
        for parameter in self.parameters():
            field_info = FieldInfo(description=parameter.description)
            if parameter.default_value is not inspect.Parameter.empty:
                field_info.default = parameter.default_value
            fields[parameter.name] = (
                parameter.type,
                field_info,
            )
        pydantic_model = create_model(model_name, **fields)

        # Generate the JSON schema from the Pydantic model.
        parameters_schema = pydantic_model.model_json_schema(mode="serialization")

        # Remove title attribute from all properties (not allowed by the Chat
        # Completions API).
        properties = parameters_schema["properties"]
        for property_key in properties:
            if "title" in properties[property_key]:
                del properties[property_key]["title"]

        # And from the top-level object.
        if "title" in parameters_schema:
            del parameters_schema["title"]

        # Output a schema that matches OpenAI's "tool" format.
        # e.g., https://platform.openai.com/docs/guides/function-calling
        # We use this because they trained GPT on it.
        schema = {
            # "$schema": "http://json-schema.org/draft-07/schema#",
            # "$id": f"urn:jsonschema:{name}",
            "name": self.name,
            "description": self.description,
            "strict": strict,
            "parameters": {
                "type": "object",
                "properties": parameters_schema["properties"],
            },
        }

        # If this is a strict schema, OpenAI requires additionalProperties to be
        # False. "strict mode" is required for JSON or structured output from
        # the API.
        if strict:
            schema["parameters"]["additionalProperties"] = False

        # Add required fields (another Chat Completions API requirement).
        if "required" in parameters_schema:
            schema["parameters"]["required"] = parameters_schema["required"]

        # Add type definitions (another Chat Completions API requirement).
        if "$defs" in parameters_schema:
            schema["parameters"]["$defs"] = parameters_schema["$defs"]
            for key in schema["parameters"]["$defs"]:
                schema["parameters"]["$defs"][key]["additionalProperties"] = False

        return schema

    async def execute(self, *args, **kwargs) -> Any:
        """
        Run this function, and return its value. If the function is a coroutine,
        it will be awaited. If string_response is True, the response will be
        converted to a string.
        """
        result = self.fn(*args, **kwargs)
        if inspect.iscoroutine(result):
            result = await result
        return result


class FunctionHandler:
    def __init__(self, tool_functions: "ToolFunctions") -> None:
        self.tool_functions = tool_functions

    def __getattr__(self, name: str) -> Callable:
        """Makes registered functions accessible as attributes of the functions object."""
        if name not in self.tool_functions.function_map:
            raise AttributeError(f"'FunctionHandler' object has no attribute '{name}'")

        async def wrapper(*args, **kwargs) -> Any:
            return await self.tool_functions.execute_function(name, args, kwargs)

        return wrapper


class ToolFunctions:
    """
    A set of tool functions that can be called from the Chat Completions API.
    Pass this into the `complete_with_tool_calls` helper function to run a full
    tool-call completion against the API.
    """

    def __init__(
        self, functions: list[ToolFunction] | None = None, with_help: bool = False
    ) -> None:
        # Set up function map.
        self.function_map: dict[str, ToolFunction] = {}
        if functions:
            for function in functions:
                self.function_map[function.name] = function

        # A help message can be generated for the function map.
        if with_help:
            self.function_map["help"] = ToolFunction(self.help)

        # This allows actions to be called as attributes.
        self.functions = FunctionHandler(self)

    def help(self) -> str:
        """Return this help message."""

        usage = [f"{command.usage()}" for command in self.function_map.values()]
        usage.sort()
        return "```text\nCommands:\n" + "\n".join(usage) + "\n```"

    def add_function(
        self,
        function: Callable,
        name: str | None = None,
        description: str | None = None,
    ) -> None:
        """Register a function with the tool functions."""
        if not name:
            name = function.__name__
        self.function_map[name] = ToolFunction(function, name, description)

    def has_function(self, name: str) -> bool:
        return name in self.function_map

    def get_function(self, name: str) -> ToolFunction | None:
        return self.function_map.get(name)

    def get_functions(self) -> list[ToolFunction]:
        return list(self.function_map.values())

    async def execute_function(
        self,
        name: str,
        args: tuple = (),
        kwargs: dict[str, Any] | None = None,
        string_response: bool = False,
    ) -> Any:
        """
        Run a function from the ToolFunctions list by name. If string_response
        is True, the function return value will be converted to a string.
        """
        if kwargs is None:
            kwargs = {}
        function = self.get_function(name)
        if not function:
            raise ValueError(f"Function {name} not found in registry.")
        response = await function.execute(*args, **kwargs)
        if string_response:
            return to_string(response)

    async def execute_function_string(
        self, function_string: str, string_response: bool = False
    ) -> Any:
        """Parse a function string and execute the function."""
        try:
            function, args, kwargs = self.parse_function_string(function_string)
        except ValueError as e:
            raise ValueError(f"{e} Type: `/help` for more information.") from e
        if not function:
            raise ValueError(
                "Function not found in registry. Type: `/help` for more information."
            )
        result = await function.execute(*args, **kwargs)
        if string_response:
            return to_string(result)

    @staticmethod
    def parse_fn_string(
        function_string: str,
    ) -> tuple[str | None, list[Any], dict[str, Any]]:
        """
        Parse a string representing a function call into its name, positional
        arguments, and keyword arguments.
        """

        # As a convenience, remove any leading slashes.
        function_string = function_string.lstrip("/")

        # As a convenience, add parentheses if they are missing.
        if " " not in function_string and "(" not in function_string:
            function_string += "()"

        # Parse the string into an AST (Abstract Syntax Tree)
        try:
            tree = ast.parse(function_string)
        except SyntaxError as err:
            raise ValueError(
                "Invalid function call. Please check your syntax."
            ) from err

        # Ensure the tree contains exactly one expression (the function call)
        if not (
            isinstance(tree, ast.Module)
            and len(tree.body) == 1
            and isinstance(tree.body[0], ast.Expr)
        ):
            raise ValueError("Expected a single function call.")

        # The function call is stored as a `Call` node within the expression
        call_node = tree.body[0].value
        if not isinstance(call_node, ast.Call):
            raise ValueError("Invalid function call. Please check your syntax.")

        # Extract the function name
        if isinstance(call_node.func, ast.Name):
            function_name = call_node.func.id
        else:
            raise ValueError("Unsupported function format. Please check your syntax.")

        # Helper function to evaluate AST nodes to their Python equivalent
        def eval_node(node):
            if isinstance(node, ast.Constant):
                return node.value
            elif isinstance(node, ast.List):
                return [eval_node(elem) for elem in node.elts]
            elif isinstance(node, ast.Tuple):
                return tuple(eval_node(elem) for elem in node.elts)
            elif isinstance(node, ast.Dict):
                return {
                    eval_node(key): eval_node(value)
                    for key, value in zip(node.keys, node.values, strict=False)
                }
            elif isinstance(node, ast.Name):
                return (
                    node.id
                )  # This can return variable names, but we assume they're constants
            elif isinstance(node, ast.BinOp):  # Handling arithmetic expressions
                return eval(compile(ast.Expression(node), filename="", mode="eval"))
            elif isinstance(node, ast.Call):
                raise ValueError("Nested function calls are not supported.")
            else:
                raise ValueError(f"Unsupported AST node type: {type(node).__name__}")

        # Extract positional arguments
        args = [eval_node(arg) for arg in call_node.args]

        # Extract keyword arguments
        kwargs = {}
        for kw in call_node.keywords:
            kwargs[kw.arg] = eval_node(kw.value)

        return function_name, args, kwargs

    def parse_function_string(
        self, function_string: str
    ) -> tuple[ToolFunction | None, list[Any], dict[str, Any]]:
        """Parse a function call string into a function and its arguments."""

        function_name, args, kwargs = ToolFunctions.parse_fn_string(function_string)
        if not function_name:
            return None, [], {}

        function = self.get_function(function_name)
        if not function:
            return None, [], {}

        return function, args, kwargs

    def chat_completion_tools(self) -> list[ChatCompletionToolParam] | NotGiven:
        """
        Return a list of ChatCompletionToolParam objects that describe the tool
        functions in this ToolFunctions object. These can be passed to the Chat
        Completions API (in the "tools" parameter) to enable tool function
        calls.
        """
        tools = [
            ChatCompletionToolParam(
                type="function", function=FunctionDefinition(**func.schema())
            )
            for func in self.function_map.values()
        ]
        return tools or NOT_GIVEN

    async def execute_tool_call(
        self, tool_call: ParsedFunctionToolCall
    ) -> ChatCompletionMessageParam | None:
        """
        Execute a function as requested by a ParsedFunctionToolCall (generated
        by the Chat Completions API) and return the response as a
        ChatCompletionMessageParam message (as required by the Chat Completions
        API)
        """
        function = tool_call.function
        if self.has_function(function.name):
            logger.debug(
                "Function call.",
                extra=add_serializable_data(
                    {"name": function.name, "arguments": function.arguments}
                ),
            )
            value: Any = None
            try:
                kwargs: dict[str, Any] = json.loads(function.arguments)
                value = await self.execute_function(
                    function.name, (), kwargs, string_response=True
                )
            except Exception as e:
                logger.error("Error.", extra=add_serializable_data({"error": e}))
                value = f"Error: {e}"
            finally:
                logger.debug(
                    "Function response.",
                    extra=add_serializable_data(
                        {"tool_call_id": tool_call.id, "content": value}
                    ),
                )
            return {
                "role": "tool",
                "content": value,
                "tool_call_id": tool_call.id,
            }
        else:
            logger.error(f"Function not found: {function.name}")
            return None


async def complete_with_tool_calls(
    async_client: AsyncOpenAI,
    completion_args: dict[str, Any],
    tool_functions: ToolFunctions,
    metadata: dict[str, Any] | None = None,
    max_tool_call_rounds: int = 5,  # Adding a parameter to limit the maximum number of rounds
) -> tuple[ParsedChatCompletion | None, list[ChatCompletionMessageParam]]:
    """
    Complete a chat response with tool calls handled by the supplied tool
    functions. This function supports multiple rounds of tool calls, continuing
    until the model no longer requests tool calls or the maximum number of rounds is reached.

    Parameters:

    - async_client: The OpenAI client.
    - completion_args: The completion arguments passed onto the OpenAI `parse`
      call. See the OpenAI API docs for more information.
    - tool_functions: A ToolFunctions object that contains the tool functions to
      be available to be called.
    - metadata: Metadata to be added to the completion response.
    - max_tool_call_rounds: Maximum number of tool call rounds to prevent infinite loops (default: 5)
    """
    if metadata is None:
        metadata = {}
    messages: list[ChatCompletionMessageParam] = completion_args.get("messages", [])
    all_new_messages: list[ChatCompletionMessageParam] = []
    current_completion = None
    rounds = 0

    # Set up the tools if tool_functions exists.
    if tool_functions:
        # Note: this overwrites any existing tools.
        completion_args["tools"] = tool_functions.chat_completion_tools()

    # Keep making completions until no more tool calls are requested
    # or we hit the maximum number of rounds
    while rounds < max_tool_call_rounds:
        rounds += 1
        round_description = f"round {rounds}"

        current_args = {**completion_args, "messages": [*messages, *all_new_messages]}
        logger.debug(
            f"Completion call ({round_description}).",
            extra=add_serializable_data(
                make_completion_args_serializable(current_args)
            ),
        )
        metadata[f"completion_request ({round_description})"] = serializable(
            current_args
        )

        # Make the completion call
        try:
            current_completion = await async_client.beta.chat.completions.parse(
                **current_args,
            )
            validate_completion(current_completion)
            logger.debug(
                f"Completion response ({round_description}).",
                extra=add_serializable_data(
                    {"completion": current_completion.model_dump()}
                ),
            )
            metadata[f"completion_response ({round_description})"] = (
                current_completion.model_dump()
            )
        except Exception as e:
            completion_error = CompletionError(e)
            metadata[f"completion_error ({round_description})"] = (
                completion_error.message
            )
            logger.error(
                completion_error.message,
                extra=add_serializable_data(
                    {"completion_error": completion_error.body, "metadata": metadata}
                ),
            )
            raise completion_error from e

        # Extract assistant message from completion and add to new messages
        assistant_message = assistant_message_from_completion(current_completion)
        if assistant_message:
            all_new_messages.append(assistant_message)

        # Check for tool calls
        completion_message = current_completion.choices[0].message
        if not completion_message.tool_calls:
            # No more tool calls, we're done
            break

        # Call all tool functions and generate return messages
        round_tool_messages: list[ChatCompletionMessageParam] = []
        for tool_call in completion_message.tool_calls:
            function_call_result_message = await tool_functions.execute_tool_call(
                tool_call
            )
            if function_call_result_message:
                round_tool_messages.append(function_call_result_message)
                all_new_messages.append(function_call_result_message)

    return current_completion, all_new_messages
