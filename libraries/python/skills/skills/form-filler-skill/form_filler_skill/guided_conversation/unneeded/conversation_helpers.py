# Copyright (c) Microsoft. All rights reserved.
# type: ignore

import time
from dataclasses import dataclass, field
from enum import StrEnum
from typing import Union


class ConversationMessageType(StrEnum):
    DEFAULT = "default"
    ARTIFACT_UPDATE = "artifact-update"
    REASONING = "reasoning"


ChatMessageContent = dataclass()


@dataclass
class Conversation:
    """An abstraction to represent a list of messages and common operations such as adding messages
    and getting a string representation.

    Args:
        conversation_messages (list[ChatMessageContent]): A list of ChatMessageContent objects.
    """

    conversation_messages: list[ChatMessageContent] = field(default_factory=list)

    def add_messages(self, messages: Union[ChatMessageContent, list[ChatMessageContent], "Conversation", None]) -> None:
        """Add a message, list of messages to the conversation or merge another conversation into the end of this one.

        Args:
            messages (Union[ChatMessageContent, list[ChatMessageContent], "Conversation"]): The message(s) to add.
                All messages will be added to the end of the conversation.

        Returns:
            None
        """
        if isinstance(messages, list):
            self.conversation_messages.extend(messages)
        elif isinstance(messages, Conversation):
            self.conversation_messages.extend(messages.conversation_messages)
        elif isinstance(messages, ChatMessageContent):  # noqa: F821
            # if ChatMessageContent.metadata doesn't have type, then add default
            if "type" not in messages.metadata:
                messages.metadata["type"] = ConversationMessageType.DEFAULT
            self.conversation_messages.append(messages)
        else:
            self.logger.warning(f"Invalid message type: {type(messages)}")
            return None

    def get_repr_for_prompt(
        self,
        exclude_types: list[ConversationMessageType] | None = None,
    ) -> str:
        """Create a string representation of the conversation history for use in LLM prompts.

        Args:
            exclude_types (list[ConversationMessageType] | None): A list of message types to exclude from the conversation
                history. If None, all message types will be included.

        Returns:
            str: A string representation of the conversation history.
        """
        if len(self.conversation_messages) == 0:
            return "None"

        # Do not include the excluded messages types in the conversation history repr.
        if exclude_types is not None:
            conversation_messages = [
                message
                for message in self.conversation_messages
                if "type" in message.metadata and message.metadata["type"] not in exclude_types
            ]
        else:
            conversation_messages = self.conversation_messages

        to_join = []
        current_turn = None
        for message in conversation_messages:
            participant_name = message.name
            # Modify the default user to be capitalized for consistency with how assistant is written.
            if participant_name == "user":
                participant_name = "User"

            # If the turn number is None, don't include it in the string
            if "turn_number" in message.metadata and current_turn != message.metadata["turn_number"]:
                current_turn = message.metadata["turn_number"]
                to_join.append(f"[Turn {current_turn}]")

            # Add the message content
            if (message.role == "assistant") and (
                "type" in message.metadata and message.metadata["type"] == ConversationMessageType.ARTIFACT_UPDATE
            ):
                to_join.append(message.content)
            elif message.role == "assistant":
                to_join.append(f"Assistant: {message.content}")
            else:
                user_string = message.content.strip()
                if user_string == "":
                    to_join.append(f"{participant_name}: <sent an empty message>")
                else:
                    to_join.append(f"{participant_name}: {user_string}")

        conversation_string = "\n".join(to_join)
        return conversation_string

    def message_to_json(self, message: ChatMessageContent) -> dict:
        """
        Convert a ChatMessageContent object to a JSON serializable dictionary.

        Args:
            message (ChatMessageContent): The ChatMessageContent object to convert to JSON.

        Returns:
            dict: A JSON serializable dictionary representation of the ChatMessageContent object.
        """
        return {
            "role": message.role,
            "content": message.content,
            "name": message.name,
            "metadata": {
                "turn_number": message.metadata["turn_number"] if "turn_number" in message.metadata else None,
                "type": message.metadata["type"] if "type" in message.metadata else ConversationMessageType.DEFAULT,
                "timestamp": message.metadata["timestamp"] if "timestamp" in message.metadata else None,
            },
        }

    def to_json(self) -> dict:
        json_data = {}
        json_data["conversation"] = {}
        json_data["conversation"]["conversation_messages"] = [
            self.message_to_json(message) for message in self.conversation_messages
        ]
        return json_data

    @classmethod
    def from_json(
        cls,
        json_data: dict,
    ) -> "Conversation":
        conversation = cls()
        for message in json_data["conversation"]["conversation_messages"]:
            conversation.add_messages(
                ChatMessageContent(
                    role=message["role"],
                    content=message["content"],
                    name=message["name"],
                    metadata={
                        "turn_number": message["metadata"]["turn_number"],
                        "type": ConversationMessageType(message["metadata"]["type"]),
                        "timestamp": message["metadata"]["timestamp"],
                    },
                )
            )

        return conversation


def create_formatted_timestamp() -> str:
    """Create a formatted timestamp."""
    return time.strftime("%Y-%m-%d %H:%M:%S", time.localtime(time.time()))
