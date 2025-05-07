import asyncio

from pydantic import BaseModel
from semantic_workbench_api_model.workbench_model import (
    NewConversationMessage,
)
from semantic_workbench_assistant.assistant_app import ConversationContext

from .model import LocalTool


class ArgumentModel(BaseModel):
    assistant_service_id: str
    template_id: str
    name: str


async def add_assistant_to_conversation(args: ArgumentModel, context: ConversationContext) -> str:
    """
    Tool to add an assistant to the conversation. Results in a conversation message that renders as a button
    for the user to click. The button will add the assistant to the conversation.
    """

    async def send_it() -> None:
        await asyncio.sleep(2)
        await context.send_messages(
            NewConversationMessage(
                content="{}",
                content_type="application/json",
                metadata={
                    "json_schema": {},
                    "ui_schema": {
                        "ui:options": {
                            "title": "Add an assistant to the conversation",
                            "submitButtonOptions": {
                                "submitText": f"Add {args.name}",
                            },
                        },
                    },
                    "appAction": {
                        "action": "addAssistant",
                        "arguments": {
                            "assistantServiceId": args.assistant_service_id,
                            "templateId": args.template_id,
                        },
                    },
                },
            )
        )

    asyncio.create_task(send_it())

    return "Success: The user will be presented with a button to add the assistant to the conversation."


tool = LocalTool(name="add_assistant_to_conversation", argument_model=ArgumentModel, func=add_assistant_to_conversation)
