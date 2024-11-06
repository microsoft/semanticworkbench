import ast
import inspect
import json
import logging
from typing import Any, Callable

from context.context import ContextProtocol
from pydantic import BaseModel

from .function import Function, Parameter


class FunctionHandler:
    def __init__(self, registry: "FunctionRegistry"):
        self.registry = registry

    def __getattr__(self, name: str) -> Callable:
        """Makes registered functions accessible as attributes of the functions object."""
        if name not in self.registry.function_map:
            raise AttributeError(f"'FunctionHandler' object has no attribute '{name}'")

        async def wrapper(*args, **kwargs) -> Any:
            return await self.registry.execute_function(name, args, kwargs)

        return wrapper


class FunctionRegistry:
    """A function registry helps manage a collection of functions that can be
    executed. Functions can be supplied on initialization or registered later.
    Additional utilities are provided, such as generating JSON schemas and
    returning results as strings."""

    def __init__(self, context: ContextProtocol, functions: list[Callable] = []) -> None:
        self.context = context

        self.function_map: dict[str, Function] = {}

        # By default, every registry has a help function.
        self.register_function(self.help, strict_schema=True)

        # But the help function can be overridden if you give it another one.
        self.register_functions(functions, strict_schema=True)

        # This allows actions to be called as attributes.
        self.functions = FunctionHandler(self)

    def help(self, context: ContextProtocol) -> str:
        """Return this help message."""
        return "Commands:\n" + "\n".join([f"{command.usage}" for command in self.function_map.values()])

    def get_function(self, name: str) -> Function | None:
        return self.function_map.get(name)

    def list_functions(self) -> list[str]:
        return list(self.function_map.keys())

    def get_functions(self) -> list[Function]:
        return [function for function in self.function_map.values()]

    def has_function(self, name: str) -> bool:
        if name == "help":
            return True
        return name in self.function_map

    def register_function(self, function: Callable, strict_schema: bool = True) -> None:
        # Ensure the first argument of the function is the context.
        if not inspect.signature(function).parameters:
            raise ValueError(f"Function {function.__name__} must have at least one parameter (context: Context).")
        if list(inspect.signature(function).parameters.keys())[0] != "context":
            raise ValueError(f"Function `{function.__name__}` must have `context` as its first parameter.")

        # Get the function's parameters and their default values.
        parameters = dict(inspect.signature(function).parameters)
        if "context" in parameters:
            del parameters["context"]
        params = [
            Parameter(
                name=param_name,
                type=param.annotation,
                description=None,  # param.annotation.description,
                default_value=param.default,
            )
            for param_name, param in parameters.items()
        ]

        self.function_map[function.__name__] = Function(
            name=function.__name__,
            description=inspect.getdoc(function) or function.__name__.replace("_", " ").title(),
            fn=function,
            parameters=params,
            strict_schema=strict_schema,
        )

    def register_functions(self, functions: list[Callable], strict_schema: bool = True) -> None:
        for function in functions:
            if function.__name__ in self.function_map:
                logging.warning(f"Function {function.__name__} already registered.")
                continue
            if not callable(function):
                raise ValueError(f"Function {function} is not callable.")
            self.register_function(function, strict_schema=strict_schema)

    async def execute_function(self, name: str, args: tuple, kwargs: dict[str, Any]) -> Any:
        """Run a registered function by name. Passes the context as the first argument."""
        function = self.get_function(name)
        if not function:
            raise ValueError(f"Function {name} not found in registry.")
        return await function.execute(self.context, *args, **kwargs)

    async def execute_function_with_string_response(self, name: str, args: tuple, kwargs: dict[str, Any]) -> str:
        """Run a registered function by name and return a string response."""
        try:
            result = await self.execute_function(name, args, kwargs)
            return __class__.to_string_response(result)
        except Exception as e:
            return f"Error running function {name}: {e}"

    async def execute_function_string(self, function_string: str) -> Any:
        """Parse a function string and execute the function."""
        try:
            function, args, kwargs = self.parse_function_string(function_string)
        except ValueError as e:
            raise ValueError(f"{e}. Type: `/help` for more information.")
        if not function:
            raise ValueError("Function not found in registry. Type: `/help` for more information.")
        return await function.execute(self.context, *args, **kwargs)

    async def execute_function_string_with_string_response(self, function_string: str) -> str:
        """Parse a function string and execute the function, returning a string response."""
        try:
            result = await self.execute_function_string(function_string)
            return __class__.to_string_response(result)
        except Exception as e:
            return f"Error running function: {e}"

    def parse_function_string(self, function_string) -> tuple[Function | None, list[Any], dict[str, Any]]:
        """Parse a function call string into a function and its arguments."""
        # As a convenience, remove any leading slashes.
        function_string = function_string.lstrip("/")

        # As a convenience, add parentheses if they are missing.
        if " " not in function_string and "(" not in function_string:
            function_string += "()"

        # Parse the string into an AST (Abstract Syntax Tree)
        try:
            tree = ast.parse(function_string)
        except SyntaxError:
            raise ValueError("Invalid function call. Please check your syntax.")

        # Ensure the tree contains exactly one expression (the function call)
        if not (isinstance(tree, ast.Module) and len(tree.body) == 1 and isinstance(tree.body[0], ast.Expr)):
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
                return {eval_node(key): eval_node(value) for key, value in zip(node.keys, node.values)}
            elif isinstance(node, ast.Name):
                return node.id  # This can return variable names, but we assume they're constants
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

        function = self.get_function(function_name)
        if not function:
            return None, [], {}

        return function, args, kwargs

    @staticmethod
    def to_string_response(result: Any) -> str:
        if result is None:
            return "Function executed successfully."
        elif isinstance(result, str):
            return result
        elif isinstance(result, (int, float)):
            return str(result)
        elif isinstance(result, dict):
            return json.dumps(result)
        elif isinstance(result, list):
            return json.dumps(result, indent=2)
        elif isinstance(result, tuple):
            return json.dumps(result)
        elif isinstance(result, BaseModel):
            return result.model_dump_json(indent=2)
        else:
            return str(result)
