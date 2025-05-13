from typing import Annotated

from pydantic import BaseModel, Field
from semantic_workbench_api_model.workbench_model import (
    MessageType,
    NewConversationMessage,
)
from semantic_workbench_assistant.assistant_app import ConversationContext

from .model import LocalTool


class ArgumentModel(BaseModel):
    assistant_service_id: str
    template_id: str

    attachments_to_copy_to_new_conversation: Annotated[
        list[str],
        Field(
            description="A list of attachment filenames to copy to the new conversation. If empty, no attachments will be copied.",
        ),
    ] = []

    introduction_message: Annotated[
        str,
        Field(
            description="The message to share with the assistant after the conversation is created. This message sets context around what the user is trying to achieve. Use your own voice, not the user's voice. Speak about the user in the third person.",
        ),
    ]


async def assistant_card(args: ArgumentModel, context: ConversationContext) -> str:
    """
    Tool to render a control that allows the user to create a new conversation with an assistant.
    Results in the app rendering an assistant card with a create buttton.
    The button will create a new conversation with the assistant.
    You can call this tool again for a difference assistant, or if the introduction message or
    attachments to copy to the new conversation should be updated.
    """

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
                        "includeAssistantIds": [context.assistant.id],
                        "newConversationMetadata": {
                            "_navigator_handoff": {
                                "introduction_message": args.introduction_message,
                                "spawned_from_conversation_id": context.id,
                                "files_to_copy": args.attachments_to_copy_to_new_conversation,
                            },
                        },
                    },
                },
            },
        )
    )

    return "Success: The user will be presented with an assistant card to create a new conversation with the assistant."


tool = LocalTool(name="assistant_card", argument_model=ArgumentModel, func=assistant_card)
