import argparse
import asyncio
import logging
from contextlib import asynccontextmanager
from dataclasses import dataclass
from typing import (
    IO,
    Annotated,
    AsyncContextManager,
    AsyncIterator,
    Callable,
    Literal,
    NoReturn,
    Optional,
)

import httpx
import pydantic
from fastapi import HTTPException, status
from pydantic import BaseModel, ConfigDict, Field
from semantic_workbench_api_model import assistant_model, workbench_model

from . import assistant_service, command, settings, storage

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
    readonly_text: Annotated[
        str,
        Field(
            title="Readonly text setting",
            description="This is a readonly text setting",
            json_schema_extra={"readOnly": True},
        ),
    ] = "read-only, informational text"
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


class CanonicalAssistant(assistant_service.FastAPIAssistantService):
    """
    Canonical implementation of a workbench assistant service.
    """

    def __init__(
        self,
        register_lifespan_handler: Callable[[Callable[[], AsyncContextManager[None]]], None],
        file_storage: storage.FileStorage,
        httpx_client_factory: Callable[[], httpx.AsyncClient] = httpx.AsyncClient,
    ) -> None:
        super().__init__(
            register_lifespan_handler=register_lifespan_handler,
            httpx_client_factory=httpx_client_factory,
            service_id="canonical-assistant.semantic-workbench",
            service_name="Canonical Assistant",
            service_description="Canonical implementation of a workbench assistant service.",
        )
        self.event_queue: asyncio.Queue[Event] = asyncio.Queue()
        self.assistant_instances = storage.ModelStorage[AssistantInstance](
            cls=AssistantInstance,
            file_storage=file_storage,
            namespace="instances",
        )

        @asynccontextmanager
        async def lifespan() -> AsyncIterator[None]:
            event_processing_task = asyncio.create_task(self.process_conversation_events())

            try:
                yield
            finally:
                event_processing_task.cancel()
                try:
                    await event_processing_task
                except asyncio.CancelledError:
                    pass
                except Exception:
                    logging.exception("event processing task raised exception")

        register_lifespan_handler(lifespan)

    async def get_service_info(self) -> assistant_model.ServiceInfoModel:
        return assistant_model.ServiceInfoModel(
            assistant_service_id=self.service_id,
            name=self.service_name,
            description=self.service_description,
            default_config=assistant_model.ConfigResponseModel(
                config=ConfigStateModel().model_dump(),
                json_schema=ConfigStateModel.model_json_schema(),
                ui_schema=config_ui_schema,
            ),
        )

    async def put_assistant(
        self,
        assistant_id: str,
        assistant: assistant_model.AssistantPutRequestModel,
        from_export: Optional[IO[bytes]] = None,
    ) -> assistant_model.AssistantResponseModel:
        instance = self.assistant_instances.get(assistant_id)
        if instance is None:
            instance = AssistantInstance(id=assistant_id, assistant_name=assistant.assistant_name, request=assistant)
        instance.assistant_name = assistant.assistant_name
        instance.request = assistant
        self.assistant_instances.set(assistant_id, instance)
        return await self.get_assistant(assistant_id=assistant_id)

    async def export_assistant_data(self, assistant_id: str) -> AssistantExportData:
        instance = self.assistant_instances.get(assistant_id)
        if instance is None:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND)

        return AssistantExportData(config=instance.config)

    async def get_assistant(self, assistant_id: str) -> assistant_model.AssistantResponseModel:
        instance = self.assistant_instances.get(assistant_id)
        if instance is None:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND)

        return assistant_model.AssistantResponseModel(id=instance.id)

    async def delete_assistant(self, assistant_id: str) -> None:
        self.assistant_instances.delete(assistant_id)

    async def get_config(self, assistant_id: str) -> assistant_model.ConfigResponseModel:
        instance = self.assistant_instances.get(assistant_id)
        if instance is None:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND)

        return assistant_model.ConfigResponseModel(
            config=instance.config.model_dump(),
            json_schema=instance.config.model_json_schema(),
            ui_schema=config_ui_schema,
        )

    async def put_config(
        self, assistant_id: str, updated_config: assistant_model.ConfigPutRequestModel
    ) -> assistant_model.ConfigResponseModel:
        instance = self.assistant_instances.get(assistant_id)
        if instance is None:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND)

        try:
            config = ConfigStateModel.model_validate(updated_config.config)
        except pydantic.ValidationError as e:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))

        for field_name, field_info in config.model_fields.items():
            if field_info.json_schema_extra and field_info.json_schema_extra.get("readOnly"):
                continue
            setattr(instance.config, field_name, getattr(config, field_name))

        self.assistant_instances.set(assistant_id, instance)

        return await self.get_config(assistant_id=assistant_id)

    async def put_conversation(
        self,
        assistant_id: str,
        conversation_id: str,
        request: assistant_model.ConversationPutRequestModel,
        from_export: Optional[IO[bytes]] = None,
    ) -> assistant_model.ConversationResponseModel:
        instance = self.assistant_instances.get(assistant_id)
        if instance is None:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND)

        conversation = Conversation(id=conversation_id, request=request, state=ConversationState())
        instance.conversations[conversation.id] = conversation

        self.assistant_instances.set(assistant_id, instance)
        return conversation.to_response()

    async def export_conversation_data(self, assistant_id: str, conversation_id: str) -> ConversationExportData:
        instance = self.assistant_instances.get(assistant_id)
        if instance is None:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND)
        conversation = instance.conversations.get(conversation_id)
        if conversation is None:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND)
        return ConversationExportData(state=conversation.state)

    async def get_conversation(
        self, assistant_id: str, conversation_id: str
    ) -> assistant_model.ConversationResponseModel:
        instance = self.assistant_instances.get(assistant_id)
        if instance is None:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND)
        if conversation_id not in instance.conversations:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND)
        conversation = instance.conversations[conversation_id]
        return conversation.to_response()

    async def delete_conversation(self, assistant_id: str, conversation_id: str) -> None:
        instance = self.assistant_instances.get(assistant_id)
        if instance is None:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND)
        instance.conversations.pop(conversation_id, None)
        self.assistant_instances.set(assistant_id, instance)

    async def get_conversation_state_descriptions(
        self, assistant_id: str, conversation_id: str
    ) -> assistant_model.StateDescriptionListResponseModel:
        instance = self.assistant_instances.get(assistant_id)
        if instance is None:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND)

        conversation = instance.conversations.get(conversation_id)
        if conversation is None:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND)

        return assistant_model.StateDescriptionListResponseModel(
            states=[
                assistant_model.StateDescriptionResponseModel(
                    id="simple_state",
                    display_name="",
                    description="",
                )
            ]
        )

    async def get_conversation_state(
        self, assistant_id: str, conversation_id: str, state_id: str
    ) -> assistant_model.StateResponseModel:
        instance = self.assistant_instances.get(assistant_id)
        if instance is None:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND)

        conversation = instance.conversations.get(conversation_id)
        if conversation is None:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND)

        if state_id != "simple_state":
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND)

        return assistant_model.StateResponseModel(
            id=state_id,
            data=conversation.state.model_dump(mode="json"),
            json_schema=conversation.state.model_json_schema(),
            ui_schema={},
        )

    async def put_conversation_state(
        self,
        assistant_id: str,
        conversation_id: str,
        state_id: str,
        updated_state: assistant_model.StatePutRequestModel,
    ) -> assistant_model.StateResponseModel:
        instance = self.assistant_instances.get(assistant_id)
        if instance is None:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND)

        conversation = instance.conversations.get(conversation_id)
        if conversation is None:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND)

        if state_id != "simple_state":
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND)

        state = conversation.state

        try:
            state.model_validate(updated_state.data)
        except pydantic.ValidationError as e:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))

        updated = state.model_copy(update=updated_state.data, deep=True)
        conversation.state = updated

        self.assistant_instances.set(assistant_id, instance)

        state_response = assistant_model.StateResponseModel(
            id=state_id,
            data=updated.model_dump(mode="json"),
            json_schema=updated.model_json_schema(),
            ui_schema={},
        )

        try:
            await self.workbench_client.for_conversation(assistant_id, conversation_id).send_conversation_state_event(
                assistant_id=assistant_id,
                state_event=workbench_model.AssistantStateEvent(
                    state_id=state_id, event="updated", state=state_response
                ),
            )
        except httpx.HTTPError as e:
            logging.exception("failed to post state event to workbench", exc_info=True)
            raise HTTPException(status_code=status.HTTP_424_FAILED_DEPENDENCY, detail=str(e))

        return state_response

    async def post_conversation_event(
        self, assistant_id: str, conversation_id: str, event: workbench_model.ConversationEvent
    ) -> None:
        instance = self.assistant_instances.get(assistant_id)
        if instance is None:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND)
        conversation = instance.conversations.get(conversation_id)
        if conversation is None:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND)

        logger.debug(
            "received conversation event; assistant_id: %s, conversation_id: %s, event: %s",
            assistant_id,
            conversation_id,
            event,
        )

        await self.event_queue.put(Event(assistant_id=assistant_id, conversation_id=conversation_id, event=event))

    async def process_conversation_events(self) -> NoReturn:
        async def _send_message(
            assistant_id: str,
            conversation_id: str,
            message_type: workbench_model.MessageType,
            message_content: str,
        ) -> None:
            instance = self.assistant_instances.get(assistant_id)
            if instance is None:
                logger.error("no assistant instance found for assistant_id: %s", assistant_id)
                return

            try:
                await self.workbench_client.for_conversation(assistant_id, conversation_id).send_messages(
                    workbench_model.NewConversationMessage(
                        message_type=message_type,
                        content=message_content,
                    )
                )
            except httpx.HTTPError as e:
                logger.error(
                    "failed to send message to workbench; assistant_id: %s, conversation_id: %s",
                    assistant_id,
                    conversation_id,
                    exc_info=e,
                )

        while True:
            try:
                try:
                    async with asyncio.timeout(1):
                        wrapper = await self.event_queue.get()
                except asyncio.TimeoutError:
                    continue

                self.event_queue.task_done()
                event = wrapper.event
                if event.event != workbench_model.ConversationEventType.message_created:
                    continue

                message = workbench_model.ConversationMessage.model_validate(event.data.get("message"))

                assistant_id = wrapper.assistant_id
                conversation_id = wrapper.conversation_id

                instance = self.assistant_instances.get(assistant_id)
                if instance is None:
                    logger.error("no assistant instance found for assistant_id: %s", assistant_id)
                    continue

                conversation = instance.conversations.get(conversation_id)
                if conversation is None:
                    logger.error(
                        "no conversation found for assistant_id: %s, conversation_id: %s", assistant_id, conversation_id
                    )
                    continue

                match message.message_type:
                    case "chat":
                        # only echo messages from users
                        if message.sender.participant_role != "user":
                            continue

                        await _send_message(
                            assistant_id=assistant_id,
                            conversation_id=conversation_id,
                            message_type=workbench_model.MessageType.chat,
                            message_content=f"echo: {message.content}",
                        )

                    case "command":
                        command = commands.get(message.command_name)
                        if command is None:
                            logger.debug("ignoring unknown command: %s", message.command_name)
                            continue

                        command_response = command.process_args(message.command_args)
                        await _send_message(
                            assistant_id=assistant_id,
                            conversation_id=conversation_id,
                            message_type=workbench_model.MessageType.command_response,
                            message_content=command_response,
                        )

            except Exception:
                logging.exception("event processing task raised exception")
                continue


app = assistant_service.create_app(
    lambda lifespan: CanonicalAssistant(
        httpx_client_factory=lambda: httpx.AsyncClient(),
        register_lifespan_handler=lifespan.register_handler,
        file_storage=storage.FileStorage(settings=settings.storage),
    )
)
