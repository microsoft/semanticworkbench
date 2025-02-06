import ast
import builtins
from typing import cast


class FunctionInterceptor(ast.NodeTransformer):
    """Transforms function calls to allow pausing on unknown functions."""

    def __init__(self) -> None:
        pass

    # def _get_function_name(self, node: Union[ast.Name, ast.Attribute]) -> str:
    #     """Build the complete function name."""
    #     try:
    #         if isinstance(node, ast.Name):
    #             return node.id
    #         elif isinstance(node, ast.Attribute):
    #             if isinstance(node.value, (ast.Name, ast.Attribute)):
    #                 base = self._get_function_name(node.value)
    #                 return f"{base}.{node.attr}"
    #             raise TypeError(f"Unsupported function name type: {type(node.value)}")
    #         raise TypeError(f"Unsupported node type for function name: {type(node)}")
    #     except Exception as e:
    #         raise RuntimeError(f"Error evaluating function name: {str(e)}")

    def get_function_name(self, node: ast.Call) -> str | None:
        """Get fully qualified function name from a Call node. Returns None for builtins."""
        if isinstance(node.func, ast.Name):
            # Special case for print - treat it as external
            if node.func.id == "print":
                return node.func.id
            # Simple function call
            if node.func.id in dir(builtins):
                return None
            return node.func.id
        elif isinstance(node.func, ast.Attribute):
            # For method calls, check if the method exists in builtin types
            method_name = node.func.attr
            if (
                method_name in dir(list)
                or method_name in dir(dict)
                or method_name in dir(set)
                or method_name in dir(str)
            ):
                return None

            # Not a builtin method, build up the full path
            parts = []
            current = node.func
            while isinstance(current, ast.Attribute):
                parts.append(current.attr)
                current = current.value
            if isinstance(current, ast.Name):
                parts.append(current.id)
                return ".".join(reversed(parts))
        return None

    def visit_Call(self, node: ast.Call) -> ast.AST:
        """Intercept function calls and wrap them in handle_function_call."""
        visited_args = [self.visit(arg) for arg in node.args]
        visited_keywords = [ast.keyword(arg=kw.arg, value=self.visit(kw.value)) for kw in node.keywords]

        if isinstance(node.func, ast.Name) and node.func.id == "ReturnValue":  # Don't transform ReturnValue calls
            return ast.Call(func=node.func, args=visited_args, keywords=visited_keywords)

        func_name = self.get_function_name(node)
        if func_name is None:
            # Builtin function/method - don't transform
            return ast.Call(func=node.func, args=visited_args, keywords=visited_keywords)

        # Transform the call
        return ast.Call(
            func=ast.Name(id="handle_function_call", ctx=ast.Load()),
            args=[cast(ast.expr, ast.Constant(value=func_name))] + visited_args,
            keywords=visited_keywords,
        )

    def visit_Return(self, node: ast.Return) -> ast.AST:
        """Transform return statements to wrap their values in ReturnValue."""
        if node.value is None:
            return ast.Return(
                value=ast.Call(
                    func=ast.Name(id="ReturnValue", ctx=ast.Load()), args=[ast.Constant(value=None)], keywords=[]
                )
            )
        return ast.Return(
            value=ast.Call(func=ast.Name(id="ReturnValue", ctx=ast.Load()), args=[self.visit(node.value)], keywords=[])
        )
