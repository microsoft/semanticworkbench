import logging
from typing import AsyncContextManager, Callable
from uuid import UUID

from semantic_workbench_api_model.workbench_model import (
    ConversationEvent,
    ConversationEventType,
    NewConversationMessage,
)
from semantic_workbench_assistant import assistant_service
from semantic_workbench_assistant.assistant_base import (
    AssistantBase,
    AssistantInstance,
    SimpleAssistantConfigStorage,
)


from . import config

logger = logging.getLogger(__name__)

# Example built on top of the Assistant base
# This example demonstrates how to extend the Assistant base
# to add additional configuration fields and UI schema for the configuration fields
# and how to create a new Assistant that uses the extended configuration model

# Comments marked with "Required", "Optional", and "Custom" indicate the type of code that follows
# Required: code that is required to be implemented for any Assistant
# Optional: code that is optional to implement for any Assistant, allowing for customization
# Custom: code that was added specifically for this example

# Modify the config.py file to add any additional configuration fields

service_id = "python-example01-assistant.python-example"
service_name = "Python Example 01 Assistant"
service_description = "A starter for building a chat assistant using the Semantic Workbench Assistant SDK."


class ChatAssistant(AssistantBase[config.AssistantConfigModel]):

    # Optional: override the __init__ method to add any additional initialization logic
    def __init__(
        self,
        register_lifespan_handler: Callable[[Callable[[], AsyncContextManager[None]]], None],
        service_id=service_id,
        service_name=service_name,
        service_description=service_description,
    ) -> None:

        super().__init__(
            register_lifespan_handler=register_lifespan_handler,
            service_id=service_id,
            service_name=service_name,
            service_description=service_description,
            config_storage=SimpleAssistantConfigStorage[config.AssistantConfigModel](
                cls=config.AssistantConfigModel,
                default_config=config.AssistantConfigModel(),
                ui_schema=config.ui_schema,
            ),
        )

    # Optional: Override the on_workbench_event method to provide custom handling of conversation events for this
    # assistant
    async def on_workbench_event(
        self,
        assistant_instance: AssistantInstance,
        event: ConversationEvent,
    ) -> None:
        # add any additional event processing logic here
        match event.event:

            case ConversationEventType.message_created | ConversationEventType.conversation_created:
                # replace the following with your own logic for processing a message created event
                return await self.respond_to_conversation(assistant_instance.id, event.conversation_id)

            case _:
                # add any additional event processing logic here
                pass

    # Custom: Implement a custom method to respond to a conversation
    async def respond_to_conversation(self, assistant_id: str, conversation_id: UUID) -> None:
        # get the conversation client
        conversation_client = self.workbench_client.for_conversation(assistant_id, str(conversation_id))

        # get the assistant's messages
        messages_response = await conversation_client.get_messages()
        if len(messages_response.messages) == 0:
            # unexpected, no messages in the conversation
            return None

        # get the last message
        last_message = messages_response.messages[-1]

        # check if the last message was sent by this assistant
        if last_message.sender.participant_id == assistant_id:
            # ignore messages from this assistant
            return

        # get the assistant's configuration, supports overwriting defaults from environment variables
        assistant_config = self._config_storage.get_with_defaults_overwritten_from_env(assistant_id)

        # add your custom logic here for generating a response to the last message
        # example: for now, just echo the last message back to the conversation

        # send a new message with the echo response
        await conversation_client.send_messages(
            NewConversationMessage(
                content=f"echo: {last_message.content}",
                metadata=(
                    {
                        "debug": {
                            "source": "echo",
                            "original_message": last_message,
                        }
                    }
                    if assistant_config.enable_debug_output
                    else None
                ),
            )
        )

    # add any additional methods or overrides here
    # see assistant_base.AssistantBase for examples


# Required: Create an instance of the Assistant class
app = assistant_service.create_app(
    lambda lifespan: ChatAssistant(
        register_lifespan_handler=lifespan.register_handler,
    )
)
