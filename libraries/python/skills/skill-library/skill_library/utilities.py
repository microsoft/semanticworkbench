import ast
import json
import re
from typing import Any

from pydantic import BaseModel


def parse_template(template: str, vars: dict[str, Any]) -> str:
    """
    Replace mustache variables in the template with the values from the arg set.
    """
    parsed_template = template
    for key, value in vars.items():
        parsed_template = parsed_template.replace(f"{{{{ {key} }}}}", str(value))
        parsed_template = parsed_template.replace(f"{{{{{key}}}}}", str(value))
    return parsed_template


def find_template_vars(text: str) -> list[str]:
    """
    Find mustache template variables in a string. Variables will be
    de-duplicated and returned in order of first appearance.
    """
    matches = re.compile(r"\{\{([a-zA-Z0-9_]+)\}\}")
    return list(set(matches.findall(text)))


def to_string(value: Any) -> str:
    """
    Convert a value to a string. This uses the json library or the Pydantic
    library when possible and falls back to str.
    """
    if value is None:
        return ""
    elif isinstance(value, str):
        return value
    elif isinstance(value, (int, float)):
        return str(value)
    elif isinstance(value, dict):
        return json.dumps(value, indent=2)
    elif isinstance(value, list):
        return json.dumps(value, indent=2)
    elif isinstance(value, tuple):
        return json.dumps(value, indent=2)
    elif isinstance(value, BaseModel):
        return value.model_dump_json(indent=2)
    else:
        return str(value)


def make_arg_set(expected_variables: list[str], args: tuple, kwargs: dict[str, Any]) -> dict[str, Any]:
    """
    Make a dictionary out of args and kwargs that aligns with expected
    variables. The result will be a dictionary containing the expected variables
    as keys and the args and kwargs as values. kwargs take precedence over args
    (they will overwrite).
    """
    arg_set = {}

    # Align any args with the expected variables.
    if args:
        for index, value in enumerate(args):
            if index < len(expected_variables):
                arg_set[expected_variables[index]] = value

    # Overwrite any args that were already set (kwargs take precedence). Only
    # include kwargs that are in the expected variables.
    kwargs_set = {key: value for key, value in kwargs.items() if key in expected_variables}
    arg_set.update(kwargs_set)
    return arg_set


def parse_command_string(command_string: str) -> tuple[str, tuple[Any, ...], dict[str, Any]]:
    """
    Parse a string representing a function call into its components (command,
    args, and kwargs).
    """

    command_string = command_string.strip()

    # As a convenience, add parentheses if they are missing.
    if " " not in command_string and "(" not in command_string:
        command_string += "()"

    # Parse the string into an AST (Abstract Syntax Tree)
    try:
        tree = ast.parse(command_string)
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
        command_name = call_node.func.id
    elif isinstance(call_node.func, ast.Attribute):
        if not isinstance(call_node.func.value, ast.Name):
            raise ValueError("Unsupported function format. Please check your syntax.")
        command_name = f"{call_node.func.value.id}.{call_node.func.attr}"
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
    args: list[Any] = [eval_node(arg) for arg in call_node.args]

    # Extract keyword arguments
    kwargs = {}
    for kw in call_node.keywords:
        kwargs[kw.arg] = eval_node(kw.value)

    return command_name, tuple(args), kwargs
