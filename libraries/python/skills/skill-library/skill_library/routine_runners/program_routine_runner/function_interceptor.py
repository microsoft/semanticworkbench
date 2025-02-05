import ast
from typing import cast


class FunctionInterceptor(ast.NodeTransformer):
    """Transforms function calls to allow pausing on unknown functions."""

    def __init__(self) -> None:
        pass

    def visit_Call(self, node: ast.Call) -> ast.AST:
        """Intercept function calls and wrap them in handle_function_call()."""
        if isinstance(node.func, ast.Name):
            return ast.Call(
                func=ast.Name(id="handle_function_call", ctx=ast.Load()),
                args=[cast(ast.expr, ast.Constant(value=node.func.id))] + [self.visit(arg) for arg in node.args],
                keywords=[ast.keyword(arg=kw.arg, value=self.visit(kw.value)) for kw in node.keywords],
            )
        return self.generic_visit(node)

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
