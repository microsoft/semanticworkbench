from enum import StrEnum

from openai.types.chat import ChatCompletionMessageParam
from pydantic import BaseModel, Field


class ConversationMessageType(StrEnum):
    DEFAULT = "default"
    ARTIFACT_UPDATE = "artifact-update"
    REASONING = "reasoning"


class Message(BaseModel):
    param: ChatCompletionMessageParam
    type: ConversationMessageType = Field(default=ConversationMessageType.DEFAULT)
    turn: int | None = None


class Conversation(BaseModel):
    messages: list[Message] = Field(default_factory=list)
    turn: int = 0

    def exclude(self, types: list[ConversationMessageType]) -> "Conversation":
        return Conversation(
            messages=[message for message in self.messages if message.type not in types], turn=self.turn
        )

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

    def add_user_message(self, content: str) -> "Conversation":
        self.messages.append(Message(param={"role": "user", "content": content}, turn=self.turn))
        return self

    def add_assistant_message(self, content: str) -> "Conversation":
        self.turn += 1
        self.messages.append(
            Message(
                param={
                    "role": "assistant",
                    "content": content,
                },
                turn=self.turn,
            )
        )
        return self
