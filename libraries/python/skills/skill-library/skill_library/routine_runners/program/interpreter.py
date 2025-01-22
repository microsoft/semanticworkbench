import ast
import logging
import pickle
from ast import AST, Assign, BinOp, Call, Constant, Expr, For, If, Name, Return, While, expr, stmt
from dataclasses import dataclass
from enum import Enum
from typing import Any, Dict, Iterable, List, Optional, Sequence, TypeVar, Union

T = TypeVar("T")


class InterpreterError(Exception):
    """Base class for interpreter-specific exceptions."""

    pass


class UnsupportedSyntaxError(InterpreterError):
    """Raised when encountering unsupported Python syntax."""

    pass


class RuntimeError(InterpreterError):
    """Raised for runtime errors during interpretation."""

    pass


class ExecutionState(Enum):
    """Represents the current state of interpreter execution."""

    RUNNING = "running"
    PAUSED = "paused"
    COMPLETED = "completed"
    ERROR = "error"


@dataclass
class FunctionCall:
    """Represents a paused function call with full type hints and validation."""

    func_name: str
    args: tuple[Any, ...]
    kwargs: Dict[str, Any]

    def __post_init__(self):
        if not isinstance(self.func_name, str):
            raise TypeError(f"func_name must be str, got {type(self.func_name)}")
        if not isinstance(self.args, tuple):
            raise TypeError(f"args must be tuple, got {type(self.args)}")
        if not isinstance(self.kwargs, dict):
            raise TypeError(f"kwargs must be dict, got {type(self.kwargs)}")


@dataclass
class ReturnValue:
    """Represents a return value from a function or block."""

    value: Any


@dataclass
class InterpreterState:
    """Represents the complete state of the interpreter."""

    variables: Dict[str, Any]
    program_counter: int
    state_stack: List[Any]
    current_function_call: Optional[FunctionCall]
    execution_state: ExecutionState


class Interpreter:
    """An improved Python interpreter with better error handling and state management."""

    def __init__(self):
        """Initialize the interpreter with a clean state."""
        self.logger = logging.getLogger(__name__)
        self._initialize_state()
        self._pending_assignment = None  # Track variable waiting for function result

    def _initialize_state(self) -> None:
        """Initialize or reset the interpreter state."""
        self.variables: Dict[str, Any] = {}
        self.program_counter: int = 0
        self.state_stack: List[Any] = []
        self.ast_nodes: List[stmt] = []
        self.current_function_call: Optional[FunctionCall] = None
        self.execution_state = ExecutionState.COMPLETED
        self._pending_assignment = None

    def load_code(self, code: str) -> None:
        """Parse and validate the AST for execution."""
        try:
            self._initialize_state()
            parsed_ast = ast.parse(code)
            self.ast_nodes = parsed_ast.body
            self.execution_state = ExecutionState.RUNNING
            self._validate_ast(parsed_ast)
        except SyntaxError as e:
            self.execution_state = ExecutionState.ERROR
            raise UnsupportedSyntaxError(f"Invalid Python syntax: {str(e)}")
        except Exception as e:
            self.execution_state = ExecutionState.ERROR
            raise InterpreterError(f"Error loading code: {str(e)}")

    def _validate_ast(self, parsed_ast: ast.AST) -> None:
        """Validate that all AST nodes are supported."""
        for node in ast.walk(parsed_ast):
            if isinstance(
                node, (ast.Import, ast.ImportFrom, ast.ClassDef, ast.AsyncFunctionDef, ast.AsyncFor, ast.AsyncWith)
            ):
                raise UnsupportedSyntaxError(f"Unsupported syntax: {type(node).__name__}")

    def get_state(self) -> InterpreterState:
        """Get the current interpreter state."""
        return InterpreterState(
            variables=self.variables.copy(),
            program_counter=self.program_counter,
            state_stack=self.state_stack.copy(),
            current_function_call=self.current_function_call,
            execution_state=self.execution_state,
        )

    def set_state(self, state: InterpreterState) -> None:
        """Set the interpreter state."""
        self.variables = state.variables
        self.program_counter = state.program_counter
        self.state_stack = state.state_stack
        self.current_function_call = state.current_function_call
        self.execution_state = state.execution_state

    def save_state(self, filename: str = "state.pkl") -> None:
        """Save the interpreter state."""
        try:
            state = self.get_state()
            with open(filename, "wb") as f:
                pickle.dump(state, f)
        except Exception as e:
            raise InterpreterError(f"Failed to save state: {str(e)}")

    def load_state(self, filename: str = "state.pkl") -> None:
        """Load the interpreter state."""
        try:
            with open(filename, "rb") as f:
                state = pickle.load(f)
            if not isinstance(state, InterpreterState):
                raise TypeError(f"Invalid state type: {type(state)}")
            self.variables = state.variables
            self.program_counter = state.program_counter
            self.state_stack = state.state_stack
            self.current_function_call = state.current_function_call
            self.execution_state = state.execution_state
        except Exception as e:
            raise InterpreterError(f"Failed to load state: {str(e)}")

    def run(self, function_return_value: Any = None) -> Union[FunctionCall, Any]:
        """Run the interpreter."""
        try:
            if self.execution_state == ExecutionState.ERROR:
                raise RuntimeError("Cannot run interpreter in error state")

            self.execution_state = ExecutionState.RUNNING

            # If we're resuming from a function call, store the result and
            # rewind program counter to retry the assignment
            if self.current_function_call and function_return_value is not None:
                # Store the function result in the target variable
                if self._pending_assignment:
                    self.variables[self._pending_assignment] = function_return_value
                    self._pending_assignment = None
                self.current_function_call = None

            while self.program_counter < len(self.ast_nodes):
                node = self.ast_nodes[self.program_counter]
                self.program_counter += 1

                result = self.interpret(node)

                if isinstance(result, FunctionCall):
                    self.current_function_call = result
                    self.execution_state = ExecutionState.PAUSED
                    return result

                if isinstance(result, ReturnValue):
                    self.execution_state = ExecutionState.COMPLETED
                    return result.value

            self.execution_state = ExecutionState.COMPLETED
            return None

        except Exception as e:
            self.execution_state = ExecutionState.ERROR
            self.logger.error(f"Runtime error: {str(e)}")
            raise RuntimeError(str(e))

    def evaluate_function_name(self, node: Union[Name, ast.Attribute]) -> str:
        """Build the complete function name."""
        try:
            if isinstance(node, ast.Name):
                return node.id
            elif isinstance(node, ast.Attribute):
                if isinstance(node.value, (ast.Name, ast.Attribute)):
                    base = self.evaluate_function_name(node.value)
                    return f"{base}.{node.attr}"
                raise TypeError(f"Unsupported function name type: {type(node.value)}")
            raise TypeError(f"Unsupported node type for function name: {type(node)}")
        except Exception as e:
            raise RuntimeError(f"Error evaluating function name: {str(e)}")

    def interpret(self, node: AST) -> Optional[Union[FunctionCall, ReturnValue]]:
        """Interpret an AST node."""
        try:
            if isinstance(node, Assign):
                return self._handle_assignment(node)
            elif isinstance(node, If):
                return self._handle_if_statement(node)
            elif isinstance(node, While):
                return self._handle_while_loop(node)
            elif isinstance(node, For):
                return self._handle_for_loop(node)
            elif isinstance(node, Expr):
                return self._handle_expression(node)
            elif isinstance(node, Return):
                return self._handle_return(node)
            else:
                raise UnsupportedSyntaxError(f"Unsupported node type: {type(node)}")
        except Exception as e:
            raise RuntimeError(f"Error interpreting node: {str(e)}")

    def _handle_assignment(self, node: Assign) -> Optional[FunctionCall]:
        """Handle variable assignment."""
        if not isinstance(node.targets[0], Name):
            raise UnsupportedSyntaxError("Only simple variable assignments are supported")
        var_name = node.targets[0].id
        value = self.evaluate(node.value)

        # If we got a FunctionCall, store the target variable name and pause
        if isinstance(value, FunctionCall):
            self._pending_assignment = var_name
            return value

        self.variables[var_name] = value
        return None

    def _handle_if_statement(self, node: If) -> None:
        """Handle if-statements with condition validation."""
        condition = self.evaluate(node.test)
        if not isinstance(condition, bool):
            raise RuntimeError(f"If condition must be boolean, got {type(condition)}")
        if condition:
            self.execute_block(node.body)
        else:
            self.execute_block(node.orelse)

    def _handle_while_loop(self, node: While) -> None:
        """Handle while-loops with condition validation."""
        while True:
            condition = self.evaluate(node.test)
            if not isinstance(condition, bool):
                raise RuntimeError(f"While condition must be boolean, got {type(condition)}")
            if not condition:
                break
            self.execute_block(node.body)

    def _handle_for_loop(self, node: For) -> None:
        """Handle for-loops with improved iterator validation."""
        if not isinstance(node.target, Name):
            raise UnsupportedSyntaxError("Only simple variable targets in for loops are supported")

        target = node.target.id
        iterable = self.evaluate(node.iter)

        if iterable is None:
            raise RuntimeError("For loop iterator cannot be None")
        if not isinstance(iterable, Iterable):
            raise RuntimeError(f"For loop iterator must be iterable, got {type(iterable)}")

        for value in iterable:
            self.variables[target] = value
            self.execute_block(node.body)

    def _handle_expression(self, node: Expr) -> Optional[FunctionCall]:
        """Handle standalone expressions."""
        result = self.evaluate(node.value)
        if isinstance(result, FunctionCall):
            return result
        return None

    def _handle_return(self, node: Return) -> ReturnValue:
        """Handle return statements."""
        return ReturnValue(self.evaluate(node.value))

    def evaluate(self, node: expr | None) -> Any:
        """Evaluate an expression."""
        if node is None:
            return None

        try:
            if isinstance(node, Constant):
                return node.value
            elif isinstance(node, Name):
                if node.id not in self.variables:
                    raise RuntimeError(f"Undefined variable: {node.id}")
                value = self.variables[node.id]
                # If the value is a FunctionCall and we have a result for it,
                # return the actual result instead
                if isinstance(value, FunctionCall) and "_last_function_result" in self.variables:
                    result = self.variables["_last_function_result"]
                    del self.variables["_last_function_result"]  # Clear after using
                    return result
                return value
            elif isinstance(node, BinOp):
                return self._evaluate_binary_operation(node)
            elif isinstance(node, Call):
                return self._evaluate_function_call(node)
            elif isinstance(node, ast.JoinedStr):
                return self._evaluate_joined_str(node)
            elif isinstance(node, ast.FormattedValue):
                return self._evaluate_formatted_value(node)
            else:
                raise UnsupportedSyntaxError(f"Unsupported expression type: {type(node)}")
        except Exception as e:
            raise RuntimeError(f"Error evaluating expression: {str(e)}")

    def _evaluate_binary_operation(self, node: BinOp) -> Any:
        """Evaluate binary operations."""
        left = self.evaluate(node.left)
        right = self.evaluate(node.right)

        op_map = {
            ast.Add: lambda x, y: x + y,
            ast.Sub: lambda x, y: x - y,
            ast.Mult: lambda x, y: x * y,
            ast.Div: lambda x, y: x / y,
            ast.FloorDiv: lambda x, y: x // y,
            ast.Mod: lambda x, y: x % y,
            ast.Pow: lambda x, y: x**y,
        }

        op_type = type(node.op)
        if op_type not in op_map:
            raise UnsupportedSyntaxError(f"Unsupported binary operator: {op_type.__name__}")

        try:
            return op_map[op_type](left, right)
        except TypeError:
            raise RuntimeError(f"Invalid operand types for {op_type.__name__}: {type(left)} and {type(right)}")
        except ZeroDivisionError:
            raise RuntimeError("Division by zero")

    def _evaluate_formatted_value(self, node: ast.FormattedValue) -> str:
        """Evaluate a formatted value within an f-string."""
        value = self.evaluate(node.value)

        # Handle format specifiers
        format_spec = ""
        if node.format_spec:
            if isinstance(node.format_spec, ast.JoinedStr):
                format_spec = self._evaluate_joined_str(node.format_spec)
            else:
                format_spec = self.evaluate(node.format_spec)

        # Apply conversion if specified
        if node.conversion == -1:  # No conversion
            converted = value
        elif node.conversion == 115:  # str
            converted = str(value)
        elif node.conversion == 114:  # repr
            converted = repr(value)
        elif node.conversion == 97:  # ascii
            converted = ascii(value)
        else:
            raise RuntimeError(f"Unknown conversion type: {node.conversion}")

        # Apply format spec if present
        if format_spec:
            return format(converted, format_spec)
        return str(converted)

    def _evaluate_joined_str(self, node: ast.JoinedStr) -> str:
        """Evaluate an f-string (JoinedStr node)."""
        parts = []
        for value in node.values:
            if isinstance(value, ast.Constant):
                parts.append(str(value.value))
            elif isinstance(value, ast.FormattedValue):
                parts.append(self._evaluate_formatted_value(value))
            else:
                raise RuntimeError(f"Unexpected node type in JoinedStr: {type(value)}")
        return "".join(parts)

    def _evaluate_function_call(self, node: Call) -> FunctionCall:
        """Evaluate function calls."""
        if not isinstance(node.func, (ast.Name, ast.Attribute)):
            raise UnsupportedSyntaxError(f"Unsupported function type: {type(node.func)}")

        func_name = self.evaluate_function_name(node.func)
        args = [self.evaluate(arg) for arg in node.args]

        # Handle keyword arguments
        kwargs = {}
        for keyword in node.keywords:
            kwargs[keyword.arg] = self.evaluate(keyword.value)

        return FunctionCall(func_name, tuple(args), kwargs)

    def execute_block(self, block: Sequence[AST]) -> None:
        """Execute a block of statements."""
        for statement in block:
            result = self.interpret(statement)
            if isinstance(result, (FunctionCall, ReturnValue)):
                raise RuntimeError("Unexpected control flow in block execution")
