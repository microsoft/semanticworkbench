import logging
from typing import IO, AsyncContextManager, Callable, TypeVar
from uuid import UUID

from fastapi import HTTPException, status
from pydantic import BaseModel, ValidationError
from semantic_workbench_api_model.assistant_model import ConfigPutRequestModel, ConfigResponseModel, ServiceInfoModel
from semantic_workbench_api_model.workbench_model import (
    ConversationEvent,
    ConversationEventType,
    NewConversationMessage,
    MessageType,
)
from semantic_workbench_assistant import assistant_service
from semantic_workbench_assistant.assistant_base import AssistantBase, AssistantInstance, file_storage
from semantic_workbench_assistant.storage import ModelStorage

from assistant.config import AssistantConfigModel

from . import config

logger = logging.getLogger(__name__)

# Example built on top of the Assistant base
# This example demonstrates how to extend the Assistant base
# to add additional configuration fields and UI schema for the configuration fields
# and how to create a new Assistant that uses the extended configuration model

# Comments marked with "Required", "Optional", and "Custom" indicate the type of code that follows
# Required: code that is required to be implemented for any Assistant
# Optional: code that is optional to implement for any Assistant, allowing for customization
# Custom: code that was added specificially for this example

# Modify the config.py file to add any additional configuration fields
ConfigT = TypeVar("ConfigT", bound=AssistantConfigModel)

service_id = "python-example01-assistant.python-example"
service_name = "Python Example 01 Assistant"
service_description = "A starter for building a chat assistant using the Semantic Workbench Assistant SDK."


class ChatAssistant(AssistantBase):

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
        )

        # Custom: initialize the assistant's configurations
        self._configs = ModelStorage[config.AssistantConfigModel](
            cls=config.AssistantConfigModel,
            file_storage=file_storage,
            namespace="configs",
        )

    # Custom: implement a custom method to validate the assistant's configurations
    async def validate_config(self, assistant_id: str, conversation_id: str) -> bool:
        assistant_config = self._get_config(assistant_id).overwrite_defaults_from_env()
        valid, message_content = assistant_config.service_config.validate_required_fields()
        if valid:
            return True

        await self.workbench_client.for_conversation(assistant_id, conversation_id).send_messages(
            NewConversationMessage(content=message_content, message_type=MessageType.notice)
        )
        return False

    # Custom: implement a custom method to store the assistant's configurations to the storage layer
    def _set_config(self, assistant_id: str, config: config.AssistantConfigModel) -> None:
        self._configs[assistant_id] = config

    def _get_config(self, assistant_id: str) -> config.AssistantConfigModel:
        return self._configs.get(assistant_id) or config.AssistantConfigModel()

    # Required: implement the get_service_info method to provide metadata about the service
    async def get_service_info(self) -> ServiceInfoModel:
        return ServiceInfoModel(
            assistant_service_id=self.service_id,
            name=self.service_name,
            description=self.service_description,
            default_config=ConfigResponseModel(
                config=config.AssistantConfigModel().model_dump(),
                json_schema=config.AssistantConfigModel.model_json_schema(),
                ui_schema=config.ui_schema,
            ),
        )

    # Required: Implement the export_assistant_data and restore_assistant_data methods to support exporting and
    # restoring assistant data, this should include the assistant's configuration and any other data that is needed
    async def export_assistant_data(
        self, assistant_id: str
    ) -> (
        assistant_service.StreamingResponse
        | assistant_service.FileResponse
        | assistant_service.JSONResponse
        | BaseModel
    ):
        """Export the assistant's data - just config for now."""
        return self._get_config(assistant_id)

    async def restore_assistant_data(self, assistant_id: str, from_export: IO[bytes]) -> None:
        """Restore the assistant's data - just config for now."""
        config_json = from_export.read().decode("utf-8")
        restored_config = config.AssistantConfigModel.model_validate_json(config_json)
        self._set_config(assistant_id, restored_config)

    # Required: Implement the get_config and put_config methods to support getting and setting the assistant's
    # configuration, see the config.py file for the configuration model and more details
    async def get_config(self, assistant_id: str) -> ConfigResponseModel:
        assistant_config = self._configs.get(assistant_id)
        if assistant_config is None:
            assistant_config = config.AssistantConfigModel()
        return ConfigResponseModel(
            config=assistant_config.model_dump(),
            json_schema=assistant_config.model_json_schema(),
            ui_schema=config.ui_schema,
        )

    async def put_config(self, assistant_id: str, updated_config: ConfigPutRequestModel) -> ConfigResponseModel:
        try:
            new_config = config.AssistantConfigModel.model_validate(updated_config.config)
        except ValidationError as e:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=e.errors())

        self._set_config(assistant_id, new_config)

        return await self.get_config(assistant_id)

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
        assistant_config = self._get_config(assistant_id).overwrite_defaults_from_env()

        # uncomment to use the OpenAI client and replace the following with your own logic for responding to a
        # conversation - please remember to practice responsible AI use
        # async with self._get_config(assistant_id).service_config.new_client() as openai_client:
        #     # replace the following with your own logic for responding to a conversation
        #     pass

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
