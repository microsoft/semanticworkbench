import argparse
import logging
from dataclasses import dataclass
from typing import Annotated, Any, Callable, Literal

from pydantic import BaseModel, ConfigDict, Field
from semantic_workbench_api_model import assistant_model, workbench_model

from . import assistant_app, command

logger = logging.getLogger(__name__)


class ModelConfigModel(BaseModel):
    name: Annotated[
        Literal["gpt35", "gpt35turbo", "gpt4"], Field(title="GPT model", description="The GPT model to use")
    ] = "gpt35turbo"


class PromptConfigModel(BaseModel):
    custom_prompt: Annotated[
        str, Field(title="Custom prompt", description="Custom prompt to use", max_length=1_000)
    ] = ""
    temperature: Annotated[float, Field(title="Temperature", description="The temperature to use", ge=0, le=1.0)] = 0.7


class ConfigStateModel(BaseModel):
    model_config: ConfigDict = ConfigDict(extra="forbid", strict=True)

    un_annotated_text: str = ""
    short_text: Annotated[
        str, Field(title="Short text setting", description="This is a short text setting", max_length=50)
    ] = ""
    long_text: Annotated[
        str, Field(title="Long text setting", description="This is a long text setting", max_length=1_000)
    ] = ""
    setting_int: Annotated[int, Field(title="Int", description="This is an int setting", ge=0, le=1_000_000)] = 0
    model: Annotated[ModelConfigModel, Field(title="Model config section")] = ModelConfigModel()
    prompt: Annotated[PromptConfigModel, Field(title="Prompt config section")] = PromptConfigModel()


config_ui_schema = {
    "long_text": {
        "ui:widget": "textarea",
    },
    "model": {
        "name": {
            "ui:widget": "radio",
        },
    },
    "prompt": {
        "custom_prompt": {
            "ui:widget": "textarea",
        },
    },
}


@dataclass
class Command:
    parser: command.CommandArgumentParser
    message_generator: Callable[[argparse.Namespace], str]

    def process_args(self, command_arg_string: str) -> str:
        try:
            parsed_args = self.parser.parse_args(command_arg_string)
        except argparse.ArgumentError as e:
            return e.message

        return self.message_generator(parsed_args)


reverse_parser = command.CommandArgumentParser(
    command="/reverse",
    description="Reverse a string",
)
reverse_parser.add_argument("string", type=str, help="the string to reverse", nargs="+")

commands = {
    reverse_parser.command: Command(parser=reverse_parser, message_generator=lambda args: " ".join(args.string)[::-1])
}


class ConversationState(BaseModel):
    message: str = "simple default state message"


class Conversation(BaseModel):
    id: str
    request: assistant_model.ConversationPutRequestModel
    state: ConversationState

    def to_response(self) -> assistant_model.ConversationResponseModel:
        return assistant_model.ConversationResponseModel(
            id=self.id,
        )


class AssistantInstance(BaseModel):
    id: str
    assistant_name: str
    config: ConfigStateModel = ConfigStateModel()
    conversations: dict[str, Conversation] = {}
    request: assistant_model.AssistantPutRequestModel


class Event(BaseModel):
    assistant_id: str
    conversation_id: str
    event: workbench_model.ConversationEvent


class AssistantExportData(BaseModel):
    config: ConfigStateModel


class ConversationExportData(BaseModel):
    state: ConversationState


class SimpleStateInspector:
    display_name = "simple state"
    description = "Simple state inspector"

    def __init__(self) -> None:
        self._data = {
            "message": "simple state message",
        }

    async def get(
        self, context: assistant_app.ConversationContext
    ) -> assistant_app.AssistantConversationInspectorDataModel:
        return assistant_app.AssistantConversationInspectorDataModel(data=self._data)

    async def set(
        self,
        context: assistant_app.ConversationContext,
        data: dict[str, Any],
    ) -> None:
        self._data = data


app = assistant_app.AssistantApp(
    assistant_service_id="canonical-assistant.semantic-workbench",
    assistant_service_name="Canonical Assistant",
    assistant_service_description="Canonical implementation of a workbench assistant service.",
    config_provider=assistant_app.BaseModelAssistantConfig(ConfigStateModel, ui_schema=config_ui_schema),
    inspectors={"simple_state": SimpleStateInspector()},
)


@app.events.conversation.message.chat.on_created
async def on_chat_message_created(
    conversation_context: assistant_app.ConversationContext,
    _: workbench_model.ConversationEvent,
    message: workbench_model.ConversationMessage,
) -> None:
    if message.sender.participant_role != "user":
        return

    await conversation_context.send_messages(workbench_model.NewConversationMessage(content=f"echo: {message.content}"))


@app.events.conversation.message.command.on_created
async def on_command_message_created(
    conversation_context: assistant_app.ConversationContext,
    _: workbench_model.ConversationEvent,
    message: workbench_model.ConversationMessage,
) -> None:
    if message.sender.participant_role != "user":
        return

    command = commands.get(message.command_name)
    if command is None:
        logger.debug("ignoring unknown command: %s", message.command_name)
        return

    command_response = command.process_args(message.command_args)
    await conversation_context.send_messages(
        workbench_model.NewConversationMessage(
            message_type=workbench_model.MessageType.command_response, content=command_response
        )
    )


app = app.fastapi_app()
