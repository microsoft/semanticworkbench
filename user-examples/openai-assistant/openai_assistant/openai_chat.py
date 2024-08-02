import logging
import re
from abc import ABC
from typing import (
    Annotated,
    Any,
    AsyncContextManager,
    Callable,
    Generic,
    Literal,
    Self,
    TypeVar,
)

import openai
import tiktoken
from openai.types.chat import ChatCompletionMessageParam
from pydantic import AliasChoices, BaseModel, ConfigDict, Field
from semantic_workbench_api_model import workbench_model
from semantic_workbench_assistant import assistant_service, config

from .chat_base import (
    AssistantInstance,
    ChatAssistantBase,
    ConfigModelBase,
    ConversationModel,
)

logger = logging.getLogger(__name__)


class AzureOpenAIServiceConfig(BaseModel):
    model_config = ConfigDict(
        title="Azure OpenAI",
        json_schema_extra={
            "required": ["azure_openai_deployment", "azure_openai_api_version"],
        },
    )

    service_type: Literal["Azure OpenAI"] = "Azure OpenAI"

    azure_openai_api_key: Annotated[
        str,
        Field(
            title="Azure OpenAI API Key",
            description=(
                "The Azure OpenAI API key for your resource instance.  If not provided, the service default will be"
                " used."
            ),
            validation_alias=AliasChoices("azure_openai_api_key", "assistant__azure_openai_api_key"),
        ),
    ] = ""

    azure_openai_endpoint: Annotated[
        str,
        Field(
            title="Azure OpenAI Endpoint",
            description=(
                "The Azure OpenAI endpoint for your resource instance. If not provided, the service default will"
                " be used."
            ),
            validation_alias=AliasChoices("azure_openai_api_key", "assistant__azure_openai_endpoint"),
        ),
    ] = ""

    azure_openai_deployment: Annotated[
        str,
        Field(
            title="Azure OpenAI Deployment",
            description="The Azure OpenAI deployment to use.",
        ),
    ] = "gpt-4-turbo"

    azure_openai_api_version: Annotated[
        str,
        Field(
            title="Azure OpenAI API Version",
            description="The Azure OpenAI API version.",
        ),
    ] = "2023-05-15"

    @property
    def openai_model(self) -> str:
        return self.azure_openai_deployment

    def validate_required_fields(self) -> tuple[bool, str]:
        if (
            self.azure_openai_endpoint
            and self.azure_openai_api_version
            and self.azure_openai_api_key
            and self.azure_openai_deployment
        ):
            return (True, "")

        return (False, "Please set the Azure OpenAI endpoint, API version, API key and deployment in the config.")

    def new_client(self) -> openai.AsyncOpenAI:
        return openai.AsyncAzureOpenAI(
            api_key=self.azure_openai_api_key,
            azure_deployment=self.azure_openai_deployment,
            api_version=self.azure_openai_api_version,
            azure_endpoint=self.azure_openai_endpoint,
        )


class OpenAIServiceConfig(BaseModel):
    model_config = ConfigDict(
        title="OpenAI",
        json_schema_extra={
            "required": ["openai_api_key", "openai_model"],
        },
    )

    service_type: Literal["OpenAI"] = "OpenAI"

    openai_api_key: Annotated[
        str,
        Field(
            title="OpenAI API Key",
            description="The API key to use for the OpenAI API.",
        ),
    ] = ""

    openai_model: Annotated[
        str,
        Field(title="OpenAI Model", description="The OpenAI model to use for generating responses."),
    ] = "gpt-4o"

    # spell-checker: ignore rocrupyvzgcl4yf25rqq6d1v
    openai_organization_id: Annotated[
        str,
        Field(
            title="Organization ID [Optional]",
            description=(
                "The ID of the organization to use for the OpenAI API.  NOTE, this is not the same as the organization"
                " name. If you do not specify an organization ID, the default organization will be used."
            ),
        ),
    ] = ""

    def validate_required_fields(self) -> tuple[bool, str]:
        if self.openai_api_key and self.openai_model:
            return (True, "")

        return (False, "Please set the OpenAI API key and model in the config.")

    def new_client(self) -> openai.AsyncOpenAI:
        return openai.AsyncOpenAI(
            api_key=self.openai_api_key,
            organization=self.openai_organization_id or None,
        )


class RequestConfig(BaseModel):
    model_config = ConfigDict(
        title="Response Generation",
    )

    max_tokens: Annotated[
        int,
        Field(
            title="Max Tokens",
            description=(
                "The maximum number of tokens to use for both the prompt and response. Current max supported by OpenAI"
                " is 128k tokens, but varies by model (https://platform.openai.com/docs/models)"
            ),
        ),
    ] = 128000

    response_tokens: Annotated[
        int,
        Field(
            title="Response Tokens",
            description=(
                "The number of tokens to use for the response, will reduce the number of tokens available for the"
                " prompt. Current max supported by OpenAI is 4096 tokens (https://platform.openai.com/docs/models)"
            ),
        ),
    ] = 4048


class OpenAIChatConfigModel(ConfigModelBase):
    model_config = ConfigDict(
        title="Assistant Configuration",
    )

    service_config: Annotated[
        AzureOpenAIServiceConfig | OpenAIServiceConfig,
        Field(
            title="Service Configuration",
            discriminator="service_type",
        ),
    ] = AzureOpenAIServiceConfig()

    request_config: Annotated[
        RequestConfig,
        Field(
            title="Request Configuration",
        ),
    ] = RequestConfig()

    enable_debug_output: Annotated[
        bool,
        Field(
            title="Enable Debug Output",
            description="Enable debug output to the conversation.",
        ),
    ] = False

    # FIXME: This name is confusing as it implies that the config values
    # are being overwritten from the environment, but it's actually
    # overwriting just the default values with the environment values.
    # The user configured values are not overwritten.
    def overwrite_from_env(self) -> Self:
        """
        Overwrite string fields that currently have their default values. Values are
        overwritten with values from environment variables or .env file. If a field
        is a BaseModel, it will be recursively updated.
        """
        updated = config.overwrite_defaults_from_env(self, prefix="assistant", separator="__")
        if updated.service_config.service_type == "Azure OpenAI":
            updated.service_config = config.overwrite_defaults_from_env(
                updated.service_config, prefix="assistant", separator="__"
            )
        else:
            updated.service_config = config.overwrite_defaults_from_env(
                updated.service_config, prefix="assistant", separator="__"
            )
        return updated


ConfigT = TypeVar("ConfigT", bound=OpenAIChatConfigModel)

openai_chat_config_ui_schema = {
    "persona_prompt": {
        "ui:widget": "textarea",
    },
    "service_config": {
        "ui:widget": "radio",
        "ui:options": {
            "hide_title": True,
        },
        "service_type": {
            "ui:widget": "hidden",
        },
        "openai_api_key": {
            "ui:widget": "password",
        },
        "openai_organization_id": {
            "ui:placeholder": "[optional]",
        },
        "azure_openai_api_key": {
            "ui:widget": "password",
            "ui:placeholder": "[optional]",
        },
        "azure_openai_endpoint": {
            "ui:placeholder": "[optional]",
        },
    },
}


class OpenAIChatAssistant(ChatAssistantBase[ConfigT], Generic[ConfigT], ABC):
    def __init__(
        self,
        register_lifespan_handler: Callable[[Callable[[], AsyncContextManager[None]]], None],
        instance_cls: type[AssistantInstance[ConfigT]] = AssistantInstance[OpenAIChatConfigModel],
        config_cls: type[ConfigT] = OpenAIChatConfigModel,
        config_ui_schema: dict[str, Any] = openai_chat_config_ui_schema,
        service_id: str = "openai-example.made-exploration",
        service_name: str = "OpenAI Example",
        service_description: str = "Simple assistant that uses OpenAI.",
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

    @property
    def respond_to_message_types(self) -> list[workbench_model.MessageType]:
        """Override to specify the message types that the assistant should respond to."""
        return [workbench_model.MessageType.chat]

    async def respond_to_conversation(self, assistant_id: str, conversation_id: str) -> None:
        instance = self.assistant_instances.get(assistant_id)
        if instance is None:
            return

        client = self.workbench_client.for_conversation(assistant_id, conversation_id)

        messages_response = await client.get_messages()

        if len(messages_response.messages) == 0:
            return

        # get the list of conversation participants
        participants_response = await client.get_participants(include_inactive=True)

        # establish a token to be used by the AI model to indicate no response
        silence_token = "{{SILENCE}}"

        system_message_content = f'{instance.config.persona_prompt}\n\nYour name is "{instance.assistant_name}".'
        if len(participants_response.participants) > 2:
            system_message_content += (
                "\n\n"
                f"There are {len(participants_response.participants)} participants in the conversation,"
                " including you as the assistant and the following users:"
                + ",".join([
                    f' "{participant.name}"'
                    for participant in participants_response.participants
                    if participant.id != assistant_id
                ])
                + "\n\nYou do not need to respond to every message. Do not respond if the last thing said was a"
                " closing statement such as 'bye' or 'goodbye', or just a general acknowledgement like 'ok' or"
                " 'thanks'. Do not respond as another user in the conversation, only as"
                f' "{instance.assistant_name}". Sometimes the other users need to talk amongst themselves and that'
                " is ok. If the conversation seems to be directed at you or the general audience, go ahead and"
                f' respond.\n\nSay "{silence_token}" to skip your turn.'
            )

        completion_messages: list[ChatCompletionMessageParam] = [{
            "role": "system",
            "content": system_message_content,
        }]

        current_tokens = 0
        current_tokens += self.get_token_count(system_message_content)  # add the system message tokens

        # consistent formatter that includes the participant name for multi-participant and name references
        def format_message(message: workbench_model.ConversationMessage) -> str:
            conversation_participant = next(
                (
                    participant
                    for participant in participants_response.participants
                    if participant.id == message.sender.participant_id
                ),
                None,
            )
            participant_name = conversation_participant.name if conversation_participant else "unknown"
            message_datetime = message.timestamp.strftime("%Y-%m-%d %H:%M:%S")
            return f"[{participant_name} - {message_datetime}]: {message.content}"

        history_messages: list[ChatCompletionMessageParam] = []
        for message in reversed(messages_response.messages):
            message_tokens = self.get_token_count(format_message(message))
            current_tokens += message_tokens
            if (
                current_tokens
                > instance.config.request_config.max_tokens - instance.config.request_config.response_tokens
            ):
                break

            if message.sender.participant_id == assistant_id:
                history_messages.append({
                    "role": "assistant",
                    "content": format_message(message),
                })
            else:
                history_messages.append({
                    "role": "user",
                    "content": format_message(message),
                })

        history_messages.reverse()
        completion_messages.extend(history_messages)

        async with self.openai_client(instance=instance) as openai_client:
            try:
                completion = await openai_client.chat.completions.create(
                    messages=completion_messages,
                    model=instance.config.service_config.openai_model,
                    max_tokens=instance.config.request_config.response_tokens,
                )
                content = completion.choices[0].message.content
                metadata = {
                    "debug": {
                        "response_generation": {
                            "request": {
                                "model": instance.config.service_config.openai_model,
                                "messages": completion_messages,
                                "max_tokens": instance.config.request_config.response_tokens,
                            },
                            "response": completion.model_dump() if completion else "[no response from openai]",
                        },
                    }
                }
            except Exception as e:
                logger.exception(f"exception occurred calling openai chat completion: {e}")
                content = "An error occurred while calling the OpenAI API."
                metadata = {
                    "debug": {
                        "response_generation": {
                            "request": {
                                "model": instance.config.service_config.openai_model,
                                "messages": completion_messages,
                            },
                            "error": str(e),
                        },
                    }
                }

        message_type = workbench_model.MessageType.chat

        if content:
            # strip out the username from the response
            if content.startswith("["):
                content = re.sub(r"\[.*\]:\s", "", content)

            # model sometimes puts extra spaces in the response, so remove them
            # when checking for the silence token
            if content.replace(" ", "") == silence_token:
                if instance.config.enable_debug_output:
                    await client.send_messages(
                        workbench_model.NewConversationMessage(
                            message_type=workbench_model.MessageType.notice,
                            content="[assistant chose to remain silent]",
                            metadata={"attribution": "debug output"},
                        )
                    )
                return

            # override message type if content starts with /
            if content.startswith("/"):
                message_type = workbench_model.MessageType.command_response

        await client.send_messages(
            workbench_model.NewConversationMessage(
                content=content or "[no response from openai]",
                message_type=message_type,
                metadata=metadata,
            )
        )

    async def process_workbench_event(
        self,
        assistant_instance: AssistantInstance[ConfigT],
        conversation: ConversationModel,
        event: workbench_model.ConversationEvent,
    ) -> None:
        try:
            if event.event != workbench_model.ConversationEventType.message_created:
                return

            message = workbench_model.ConversationMessage.model_validate(event.data.get("message"))

            # only respond to specific message types
            if message.message_type not in self.respond_to_message_types:
                return

            # don't respond to messages from the assistant
            if message.sender.participant_id == assistant_instance.id:
                return

            if not await self.validate_config(assistant_id=assistant_instance.id, conversation_id=conversation.id):
                return

            client = self.workbench_client.for_conversation(assistant_instance.id, conversation.id)

            await client.update_participant_me(workbench_model.UpdateParticipant(status="thinking..."))
            try:
                await self.respond_to_conversation(assistant_id=assistant_instance.id, conversation_id=conversation.id)
            finally:
                await client.update_participant_me(workbench_model.UpdateParticipant(status=None))

        except Exception:
            logging.exception("exception in process_conversation_events loop")

    async def validate_config(self, assistant_id: str, conversation_id: str) -> bool:
        instance = self.assistant_instances[assistant_id]
        config = instance.config.overwrite_from_env()

        valid, msg = config.service_config.validate_required_fields()
        if valid:
            return True

        await self.workbench_client.for_conversation(assistant_id, conversation_id).send_messages(
            workbench_model.NewConversationMessage(
                content=msg,
            )
        )
        return False

    def openai_client(self, instance: AssistantInstance[ConfigT]) -> openai.AsyncOpenAI:
        config = instance.config.overwrite_from_env()
        return config.service_config.new_client()

    def get_token_count(self, string: str) -> int:
        encoding = tiktoken.get_encoding("cl100k_base")
        return len(encoding.encode(string))


app = assistant_service.create_app(
    lambda lifespan: OpenAIChatAssistant(
        register_lifespan_handler=lifespan.register_handler,
    )
)
