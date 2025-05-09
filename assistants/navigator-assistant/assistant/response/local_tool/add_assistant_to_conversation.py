import asyncio

from pydantic import BaseModel
from semantic_workbench_api_model.workbench_model import (
    MessageType,
    NewConversationMessage,
)
from semantic_workbench_assistant.assistant_app import ConversationContext

from .model import LocalTool


class ArgumentModel(BaseModel):
    assistant_service_id: str
    template_id: str


async def assistant_card(args: ArgumentModel, context: ConversationContext) -> str:
    """
    Tool to render a control that allows the user to create a new conversation with an assistant.
    Results in the app rendering an assistant card with a create buttton.
    The button will create a new conversation with the assistant.
    """

    async def send_it() -> None:
        await asyncio.sleep(2)
        await context.send_messages(
            NewConversationMessage(
                message_type=MessageType.note,
                content="Click the button below to add the assistant to the conversation.",
                metadata={
                    "_appComponent": {
                        "type": "AssistantCard",
                        "props": {
                            "assistantServiceId": args.assistant_service_id,
                            "templateId": args.template_id,
                        },
                    },
                },
            )
        )

    asyncio.create_task(send_it())

    return "Success: The user will be presented with an assistant card to create a new conversation with the assistant."


tool = LocalTool(name="assistant_card", argument_model=ArgumentModel, func=assistant_card)
