import logging
from abc import ABC
from typing import Any, AsyncContextManager, Callable, Generic, TypeVar

from semantic_workbench_assistant import assistant_service
from openai_assistant import chat_base, openai_chat

from assistant.config import AssistantConfigModel, assistant_config_ui_schema

logger = logging.getLogger(__name__)

# Example built on top of the OpenAI Chat Assistant
# This example demonstrates how to extend the OpenAI Chat Assistant
# to add additional configuration fields and UI schema for the configuration fields
# and how to create a new Chat Assistant that uses the extended configuration model

# If you are not using OpenAI Chat Assistant, you can replace the openai_chat.*
# imports with the appropriate imports for the Chat Assistant you are using


# Modify the config.py file to add any additional configuration fields
ConfigT = TypeVar("ConfigT", bound=AssistantConfigModel)


class ChatAssistant(openai_chat.OpenAIChatAssistant, Generic[ConfigT], ABC):

    def __init__(
        self,
        register_lifespan_handler: Callable[[Callable[[], AsyncContextManager[None]]], None],
        instance_cls: type[chat_base.AssistantInstance[ConfigT]] = chat_base.AssistantInstance[AssistantConfigModel],
        config_cls: type[ConfigT] = AssistantConfigModel,
        config_ui_schema: dict[str, Any] = assistant_config_ui_schema,
        service_id="quickstart-assistant.made-exploration",
        service_name="Quickstart Chat Assistant",
        service_description="A starter for building a chat assistant using the Semantic Workbench Assistant SDK.",
    ) -> None:

        super().__init__(
            register_lifespan_handler=register_lifespan_handler,
            instance_cls=instance_cls,
            config_cls=config_cls,
            config_ui_schema=config_ui_schema,
            service_id=service_id,
            service_name=service_name,
            service_description=service_description,
        )

    # add any additional methods or overrides here
    # see openai_chat.OpenAIChatAssistant and chat_base.ChatAssistantBase for examples


app = assistant_service.create_app(
    lambda lifespan: ChatAssistant(
        register_lifespan_handler=lifespan.register_handler,
    )
)
