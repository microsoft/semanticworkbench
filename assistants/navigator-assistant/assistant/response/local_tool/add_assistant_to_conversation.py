import logging
from textwrap import dedent
from typing import Annotated

from pydantic import BaseModel, Field
from semantic_workbench_api_model.workbench_model import (
    MessageType,
    NewConversationMessage,
)
from semantic_workbench_assistant.assistant_app import ConversationContext

from .list_assistant_services import get_navigator_visible_assistant_service_templates
from .model import LocalTool

logger = logging.getLogger(__name__)


class ArgumentModel(BaseModel):
    assistant_service_id: str
    template_id: str

    introduction_message: Annotated[
        str,
        Field(
            description=dedent("""
            The message to share with the assistant after it is added to the conversation.
            This message sets context around what the user is trying to achieve.
            Use your own voice, as the navigator assistant. Speak about the user in the third person.
            For example: "{{the user's name}} is trying to get help with their project. They are looking for a way to..."
            """).strip(),
        ),
    ]


async def assistant_card(args: ArgumentModel, context: ConversationContext) -> str:
    """
    Tool to render a control that allows the user to add an assistant to this conversation.
    Results in the app rendering an assistant card with a "+" buttton.
    This tool does not add the assistant to the conversation. The assistant will be added to
    the conversation if the user clicks the "+" button.
    You can call this tool again for a different assistant, or if the introduction message
    should be updated.
    """

    # check if the assistant service id is valid
    service_templates = await get_navigator_visible_assistant_service_templates(context)
    if not any(
        template
        for (service_id, template, _) in service_templates
        if service_id == args.assistant_service_id and template.id == args.template_id
    ):
        logger.warning(
            "assistant_card tool called with invalid assistant_service_id or template_id; assistant_service_id: %s, template_id: %s",
            args.assistant_service_id,
            args.template_id,
        )
        return (
            "Error: The selected assistant_service_id and template_id are not available. For reference, the available assistants are:\n\n"
            + "\n\n".join([
                f"assistant_service_id: {assistant_service_id}, template_id: {template.id}\nname: {template.name}\n\n"
                for assistant_service_id, template, _ in service_templates
            ])
        )

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
                        "existingConversationId": context.id,
                        "participantMetadata": {
                            "_navigator_handoff": {
                                "introduction_message": args.introduction_message,
                                "spawned_from_conversation_id": context.id,
                            },
                        },
                    },
                },
            },
        )
    )

    return "Success: The user will be presented with an assistant card to add the assistant to the conversation."


tool = LocalTool(name="assistant_card", argument_model=ArgumentModel, func=assistant_card)
