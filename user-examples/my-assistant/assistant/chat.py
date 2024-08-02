import logging
from abc import ABC
import re
from typing import Any, AsyncContextManager, Callable, Generic, TypeVar

from openai.types import chat
from pydantic import BaseModel
from semantic_workbench_assistant import assistant_service, settings
from semantic_workbench_assistant.storage import FileStorage, FileStorageSettings
from semantic_workbench_api_model import workbench_model
from openai_assistant import chat_base, openai_chat

from assistant.agents.attachment_agent import AttachmentAgent
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
        service_id="my-assistant.made-exploration",
        service_name="My Chat Assistant",
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

    class ResponseHandlerParameters(BaseModel):
        instance: chat_base.AssistantInstance[AssistantConfigModel]
        assistant_id: str
        conversation_id: str
        message_list: workbench_model.ConversationMessageList

    async def respond_to_conversation(self, assistant_id: str, conversation_id: str) -> None:
        instance: chat_base.AssistantInstance[AssistantConfigModel] | None = self.assistant_instances.get(assistant_id)
        if instance is None:
            return

        client = self.workbench_client.for_conversation(assistant_id, conversation_id)

        messages_response = await client.get_messages()

        if len(messages_response.messages) == 0:
            return

        response_handler_params = self.ResponseHandlerParameters(
            instance=instance,
            assistant_id=assistant_id,
            conversation_id=conversation_id,
            message_list=messages_response,
        )

        await self.open_chat_response_handler(response_handler_params)

    async def open_chat_response_handler(
        self,
        params: ResponseHandlerParameters,
    ) -> None:
        client = self.workbench_client.for_conversation(params.assistant_id, params.conversation_id)

        # get the list of conversation participants
        participants_response = await client.get_participants(include_inactive=True)

        # establish a token to be used by the AI model to indicate no response
        silence_token = "{{SILENCE}}"

        system_message_content = (
            f'{params.instance.config.persona_prompt}\n\nYour name is "{params.instance.assistant_name}".'
        )
        if len(participants_response.participants) > 2:
            system_message_content += (
                "\n\n"
                f"There are {len(participants_response.participants)} participants in the conversation,"
                " including you as the assistant and the following users:"
                + ",".join([
                    f' "{participant.name}"'
                    for participant in participants_response.participants
                    if participant.id != params.assistant_id
                ])
                + "\n\nYou do not need to respond to every message. Do not respond if the last thing said was a"
                " closing statement such as 'bye' or 'goodbye', or just a general acknowledgement like 'ok' or"
                " 'thanks'. Do not respond as another user in the conversation, only as"
                f' "{params.instance.assistant_name}". Sometimes the other users need to talk'
                " amongst themselves and that is ok. If the conversation seems to be directed at you or the general"
                f' audience, go ahead and respond.\n\nSay "{silence_token}" to skip your turn.'
            )

        completion_messages: list[chat.ChatCompletionMessageParam] = [{
            "role": "system",
            "content": system_message_content,
        }]

        current_tokens = 0
        current_tokens += self.get_token_count(system_message_content)  # add the system message tokens

        if params.instance.config.agents_config.attachment_agent.include_in_response_generation:
            file_storage = self.get_file_storage_for_conversation(params.assistant_id, params.conversation_id)
            attachment_agent = AttachmentAgent(client, file_storage)
            attachment_messages = await attachment_agent.generate_attachment_messages()
            if len(attachment_messages) > 0:
                completion_messages.append({
                    "role": "system",
                    "content": params.instance.config.agents_config.attachment_agent.context_description,
                })
                completion_messages.extend(attachment_messages)

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

        history_messages: list[chat.ChatCompletionMessageParam] = []
        for message in reversed(params.message_list.messages):
            message_tokens = self.get_token_count(format_message(message))
            current_tokens += message_tokens
            if (
                current_tokens
                > params.instance.config.request_config.max_tokens
                - params.instance.config.request_config.response_tokens
            ):
                break

            if message.sender.participant_id == params.assistant_id:
                history_messages.append({
                    "role": "assistant",
                    "content": format_message(message),
                })
            else:
                history_messages.append({
                    "role": "user",
                    "content": format_message(message),
                })
                if message.filenames and len(message.filenames) > 0:
                    history_messages.append({
                        "role": "system",
                        "content": f"User attached files: {', '.join(message.filenames)}",
                    })

        history_messages.reverse()
        completion_messages.extend(history_messages)
        total_tokens_from_completion: None | int = None

        async with self.openai_client(instance=params.instance) as openai_client:
            try:
                completion = await openai_client.chat.completions.create(
                    messages=completion_messages,
                    model=params.instance.config.service_config.openai_model,
                    max_tokens=params.instance.config.request_config.response_tokens,
                )
                content = completion.choices[0].message.content
                metadata = {
                    "debug": {
                        "response_generation": {
                            "request": {
                                "model": params.instance.config.service_config.openai_model,
                                "messages": completion_messages,
                                "max_tokens": params.instance.config.request_config.response_tokens,
                            },
                            "response": completion.model_dump() if completion else "[no response from openai]",
                        },
                    }
                }
                total_tokens_from_completion = completion.usage.total_tokens if completion.usage else None
            except Exception as e:
                logger.exception(f"exception occurred calling openai chat completion: {e}")
                content = "An error occurred while calling the OpenAI API."
                metadata = {
                    "debug": {
                        "response_generation": {
                            "request": {
                                "model": params.instance.config.service_config.openai_model,
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
                if params.instance.config.enable_debug_output:
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

        # check the token usage and send a warning if it is high
        if total_tokens_from_completion is not None and params.instance.config.high_token_usage_warning.enabled:
            token_count_for_warning = params.instance.config.request_config.max_tokens * (
                params.instance.config.high_token_usage_warning.threshold / 100
            )
            if total_tokens_from_completion > token_count_for_warning:
                await client.send_messages(
                    workbench_model.NewConversationMessage(
                        content=params.instance.config.high_token_usage_warning.message,
                        message_type=workbench_model.MessageType.notice,
                    )
                )

    async def process_workbench_event(
        self,
        assistant_instance: chat_base.AssistantInstance[AssistantConfigModel],
        conversation: chat_base.ConversationModel,
        event: workbench_model.ConversationEvent,
    ) -> None:
        if event.event == workbench_model.ConversationEventType.participant_created:
            return await self.process_workbench_participant_created_event(assistant_instance, conversation, event)

        if (
            event.event == workbench_model.ConversationEventType.file_created
            or event.event == workbench_model.ConversationEventType.file_updated
            or event.event == workbench_model.ConversationEventType.file_deleted
        ):
            return await self.process_workbench_file_event(assistant_instance, conversation, event)

        return await super().process_workbench_event(assistant_instance, conversation, event)

    async def process_workbench_participant_created_event(
        self,
        assistant_instance: chat_base.AssistantInstance[AssistantConfigModel],
        conversation: chat_base.ConversationModel,
        event: workbench_model.ConversationEvent,
    ) -> None:
        # check if the participant is the assistant, if so send a welcome message
        if event.data.get("participant", {}).get("id") != assistant_instance.id:
            # not the assistant, so ignore
            return

        client = self.workbench_client.for_conversation(assistant_instance.id, conversation.id)

        # send a welcome message to the conversation
        await client.send_messages(
            workbench_model.NewConversationMessage(
                content=assistant_instance.config.welcome_message,
                message_type=workbench_model.MessageType.chat,
                metadata={"debug": "welcome message from configuration"},
            )
        )

    async def process_workbench_file_event(
        self,
        assistant_instance: chat_base.AssistantInstance[AssistantConfigModel],
        conversation: chat_base.ConversationModel,
        event: workbench_model.ConversationEvent,
    ) -> None:
        client = self.workbench_client.for_conversation(assistant_instance.id, conversation.id)
        file_storage = self.get_file_storage_for_conversation(assistant_instance.id, conversation.id)
        attachment_agent = AttachmentAgent(client, file_storage)

        file_data = event.data.get("file")
        if file_data is None:
            logger.error("event is missing file")
            return
        file = workbench_model.File.model_validate(file_data)

        if (
            event.event == workbench_model.ConversationEventType.file_created
            or event.event == workbench_model.ConversationEventType.file_updated
        ):
            await client.update_participant_me(
                workbench_model.UpdateParticipant(
                    status="processing attachment(s)...",
                )
            )
            try:
                await attachment_agent.set_attachment_content_from_file(file)
            except Exception as e:
                logger.exception(f"exception occurred processing attachment: {e}")
                await client.send_messages(
                    workbench_model.NewConversationMessage(
                        content=f"There was an error processing the attachment ({file.filename}): {e}",
                        message_type=workbench_model.MessageType.chat,
                        metadata={"attribution": "system"},
                    )
                )
            finally:
                await client.update_participant_me(
                    workbench_model.UpdateParticipant(
                        status=None,
                    )
                )
        elif event.event == workbench_model.ConversationEventType.file_deleted:
            attachment_agent.delete_attachment_for_file(file)

    async def get_recent_message_type_history(
        self,
        assistant_id: str,
        conversation_id: str,
        message_types: list[workbench_model.MessageType] = [
            workbench_model.MessageType.chat,
            workbench_model.MessageType.note,
            workbench_model.MessageType.notice,
            workbench_model.MessageType.command,
            workbench_model.MessageType.command_response,
        ],
        limit=10,
    ) -> list[workbench_model.ConversationMessage]:
        instance = self.assistant_instances.get(assistant_id)
        if instance is None:
            raise Exception("Assistant instance not found")

        messages_response = await self.workbench_client.for_conversation(assistant_id, conversation_id).get_messages(
            message_types=message_types, limit=limit
        )

        return messages_response.messages

    def get_file_storage_for_conversation(self, assistant_id: str, conversation_id: str) -> FileStorage:
        root = settings.storage.root
        return FileStorage(FileStorageSettings(root=f"{root}/files/{assistant_id}/{conversation_id}"))


app = assistant_service.create_app(
    lambda lifespan: ChatAssistant(
        register_lifespan_handler=lifespan.register_handler,
    )
)
