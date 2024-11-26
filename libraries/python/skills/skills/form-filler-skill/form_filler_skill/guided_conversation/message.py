from enum import StrEnum

from attr import dataclass
from openai.types.chat import ChatCompletionMessageParam
from pydantic import BaseModel


class ConversationMessageType(StrEnum):
    DEFAULT = "default"
    ARTIFACT_UPDATE = "artifact-update"
    REASONING = "reasoning"


class Message(BaseModel):
    def __init__(
        self,
        chat_completion_message_param: ChatCompletionMessageParam,
        type: ConversationMessageType | None = None,
        turn: int | None = None,
    ) -> None:
        self.param = chat_completion_message_param
        self.turn = turn
        self.type = type or ConversationMessageType.DEFAULT


@dataclass
class Conversation(BaseModel):
    messages: list[Message] = []

    def exclude(self, types: list[ConversationMessageType]) -> list[Message]:
        return [message for message in self.messages if message.type not in types]

    def __str__(self) -> str:
        message_strs = []
        current_turn = None
        for message in self.messages:
            # Modify the default user to be capitalized for consistency with how
            # assistant is written.
            name = message.param["role"]
            if name == "user":
                name = "User"

            # Append the turn number if it has changed.
            if message.turn is not None and current_turn != message.turn:
                current_turn = message.turn
                message_strs.append(f"[Turn {current_turn}]")

            # Append the message content.
            content = message.param.get("content", "")
            if message.param["role"] == "assistant":
                if message.type == ConversationMessageType.ARTIFACT_UPDATE:
                    message_strs.append(content)
                else:
                    message_strs.append(f"Assistant: {content}")
            else:
                user_string = str(content).strip()
                if user_string == "":
                    message_strs.append(f"{name}: <sent an empty message>")
                else:
                    message_strs.append(f"{name}: {user_string}")

        return "\n".join(message_strs)
