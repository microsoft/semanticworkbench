import ast
import inspect
from dataclasses import dataclass
from typing import Any, Callable


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


class Action:
    """
    A tool function is a Python function that can be called as a tool from the
    chat completion API. This class wraps a function so you can generate it's
    JSON schema for the chat completion API, execute it with arguments, and
    generate a usage string (for help messages)
    """

    def __init__(self, fn: Callable, name: str | None = None, description: str | None = None) -> None:
        self.fn = fn
        self.name = name or fn.__name__
        self.description = description or inspect.getdoc(fn) or self.name.replace("_", " ").title()

    def parameters(self, exclude: list[str] = []) -> list[Parameter]:
        """
        This function's parameters and their default values.
        """
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


class ActionHandler:
    def __init__(self, actions: "Actions") -> None:
        self.actions = actions

    def __getattr__(self, name: str) -> Callable:
        """Makes registered functions accessible as attributes of the functions object."""
        if name not in self.actions.action_map:
            raise AttributeError(f"'Actions' object has no attribute '{name}'")

        async def wrapper(*args, **kwargs) -> Any:
            return await self.actions.execute_action(name, args, kwargs)

        return wrapper


class Actions:
    """
    A set of tool functions that can be called from the Chat Completions API.
    Pass this into the `complete_with_tool_calls` helper function to run a full
    tool-call completion against the API.
    """

    def __init__(self, actions: list[Action] | None = None, with_help: bool = False) -> None:
        # Set up function map.
        self.action_map = {}
        if actions:
            for function in actions:
                self.action_map[function.name] = function

        # A help message can be generated for the function map.
        if with_help:
            self.action_map["help"] = Action(self.help)

        # This allows actions to be called as attributes.
        self.functions = ActionHandler(self)

    def help(self) -> str:
        """Return this help message."""

        usage = [f"{command.usage()}" for command in self.action_map.values()]
        usage.sort()
        return "Commands:\n" + "\n".join(usage)

    def add_function(self, function: Callable, name: str | None = None, description: str | None = None) -> None:
        """Register a function as an action."""
        if not name:
            name = function.__name__
        self.action_map[name] = Action(function, name, description)

    def add_functions(self, functions: list[Callable]) -> None:
        """Register a list of functions as actions."""
        for function in functions:
            self.add_function(function)

    def has_action(self, name: str) -> bool:
        return name in self.action_map

    def get_action(self, name: str) -> Action | None:
        return self.action_map.get(name)

    def get_actions(self) -> list[Action]:
        return [function for function in self.action_map.values()]

    async def execute_action(
        self,
        name: str,
        args: tuple = (),
        kwargs: dict[str, Any] = {},
    ) -> Any:
        """
        Run a function from the ToolFunctions list by name. If string_response
        is True, the function return value will be converted to a string.
        """
        function = self.get_action(name)
        if not function:
            raise ValueError(f"Function {name} not found in registry.")
        return await function.execute(*args, **kwargs)

    async def execute_action_string(self, function_string: str) -> Any:
        """Parse a function string and execute the function."""
        try:
            function, args, kwargs = self.parse_action_string(function_string)
        except ValueError as e:
            raise ValueError(f"{e}. Type: `/help` for more information.")
        if not function:
            raise ValueError("Function not found in registry. Type: `/help` for more information.")
        return await function.execute(*args, **kwargs)

    def parse_action_string(self, action_string: str) -> tuple[Action | None, list[Any], dict[str, Any]]:
        """Parse a function call string into a function and its arguments."""

        # As a convenience, remove any leading slashes.
        action_string = action_string.lstrip("/")

        # As a convenience, add parentheses if they are missing.
        if " " not in action_string and "(" not in action_string:
            action_string += "()"

        # Parse the string into an AST (Abstract Syntax Tree)
        try:
            tree = ast.parse(action_string)
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
            action_name = call_node.func.id
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

        action = self.get_action(action_name)
        if not action:
            return None, [], {}

        return action, args, kwargs
