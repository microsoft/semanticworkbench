from typing import Awaitable, Callable, Generic, TypeVar

from attr import dataclass
from openai.types.chat import ChatCompletionToolParam
from openai.types.shared_params import FunctionDefinition
from pydantic import BaseModel
from semantic_workbench_assistant.assistant_app import ConversationContext

ToolArgumentModelT = TypeVar("ToolArgumentModelT", bound=BaseModel)


@dataclass
class LocalTool(Generic[ToolArgumentModelT]):
    name: str
    argument_model: type[ToolArgumentModelT]
    func: Callable[[ToolArgumentModelT, ConversationContext], Awaitable[str]]
    description: str = ""

    def to_chat_completion_tool(self) -> ChatCompletionToolParam:
        parameters = self.argument_model.model_json_schema()
        return ChatCompletionToolParam(
            type="function",
            function=FunctionDefinition(
                name=self.name, description=self.description or self.func.__doc__ or "", parameters=parameters
            ),
        )
