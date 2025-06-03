from typing import Any, Awaitable, Callable, Generic, TypeVar

from attr import dataclass
from pydantic import BaseModel, ValidationError
from semantic_workbench_assistant.assistant_app import ConversationContext

from ..utils import ExecutableTool

ToolArgumentModelT = TypeVar("ToolArgumentModelT", bound=BaseModel)


@dataclass
class LocalTool(Generic[ToolArgumentModelT]):
    name: str
    argument_model: type[ToolArgumentModelT]
    func: Callable[[ToolArgumentModelT, ConversationContext], Awaitable[str]]
    description: str = ""

    def to_executable(self) -> ExecutableTool:
        async def func(context: ConversationContext, arguments: dict[str, Any]) -> str:
            try:
                typed_argument = self.argument_model.model_validate(arguments)
            except ValidationError as e:
                content = f"Error validating local tool call arguments: {e}"
            else:
                content = await self.func(typed_argument, context)

            return content

        return ExecutableTool(
            name=self.name,
            description=self.description or self.func.__doc__ or "",
            parameters=self.argument_model.model_json_schema(),
            func=func,
        )
