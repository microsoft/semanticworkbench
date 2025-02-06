from openai.types.chat import ChatCompletionMessageParam, ChatCompletionUserMessageParam
from openai_client.chat_driver import MessageHistoryProviderProtocol
from semantic_workbench_api_model.workbench_model import (
    ConversationMessageList,
    MessageType,
    NewConversationMessage,
)
from semantic_workbench_assistant.assistant_app import (
    ConversationContext,
)


class WorkbenchMessageProvider(MessageHistoryProviderProtocol):
    """
    This class is used to use the workbench for messages.
    """

    def __init__(self, session_id: str, conversation_context: ConversationContext) -> None:
        self.session_id = session_id
        self.conversation_context = conversation_context

    async def get(self) -> list[ChatCompletionMessageParam]:
        message_list: ConversationMessageList = await self.conversation_context.get_messages()
        return [
            ChatCompletionUserMessageParam(
                role="user",
                content=message.content,
            )
            for message in message_list.messages
            if message.message_type == MessageType.chat
        ]

    async def append(self, message: ChatCompletionMessageParam) -> None:
        if "content" in message:
            await self.conversation_context.send_messages(
                NewConversationMessage(
                    content=str(message["content"]),
                    message_type=MessageType.chat,
                )
            )

    async def get_history(self) -> ConversationMessageList:
        return await self.conversation_context.get_messages()

    async def get_history_json(self) -> str:
        message_list: ConversationMessageList = await self.conversation_context.get_messages()
        return message_list.model_dump_json()
