import logging
import re
from typing import AsyncContextManager, Callable
from uuid import UUID

import tiktoken
import openai
from openai.types import chat
from semantic_workbench_api_model.workbench_model import (
    ConversationEvent,
    ConversationEventType,
    NewConversationMessage,
    MessageType,
    UpdateParticipant,
)
from semantic_workbench_assistant import assistant_service, settings
from semantic_workbench_assistant.assistant_base import (
    AssistantBase,
    AssistantInstance,
    SimpleAssistantConfigStorage,
)
from semantic_workbench_assistant.storage import FileStorage, FileStorageSettings
from semantic_workbench_api_model import workbench_model

from assistant.agents.attachment_agent import AttachmentAgent

from . import config

logger = logging.getLogger(__name__)

service_id = "my-assistant.made-exploration"
service_name = "My Chat Assistant"
service_description = "A sample chat assistant using the Semantic Workbench Assistant SDK."


class ChatAssistant(AssistantBase):

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

    async def validate_config(self, assistant_id: str, conversation_id: str) -> bool:
        assistant_config = self._config_storage.get_with_defaults_overwritten_from_env(assistant_id)
        valid, message_content = assistant_config.service_config.validate_required_fields()
        if valid:
            return True

        await self.workbench_client.for_conversation(assistant_id, conversation_id).send_messages(
            NewConversationMessage(content=message_content, message_type=MessageType.notice)
        )
        return False

    async def on_workbench_event(
        self,
        assistant_instance: AssistantInstance,
        event: ConversationEvent,
    ) -> None:
        match event.event:

            case ConversationEventType.participant_created:
                return await self.process_workbench_participant_created_event(
                    assistant_instance.id, event.conversation_id, event
                )

            case ConversationEventType.message_created | ConversationEventType.conversation_created:
                # get the conversation client
                conversation_client = self.workbench_client.for_conversation(
                    assistant_instance.id, str(event.conversation_id)
                )
                # update the participant status to indicate the assistant is thinking
                await conversation_client.update_participant_me(UpdateParticipant(status="thinking..."))
                try:
                    # replace the following with your own logic for processing a message created event
                    await self.respond_to_conversation(assistant_instance.id, event.conversation_id)
                finally:
                    # update the participant status to indicate the assistant is done thinking
                    await conversation_client.update_participant_me(UpdateParticipant(status=None))
                return

            case (
                ConversationEventType.file_created
                | ConversationEventType.file_updated
                | ConversationEventType.file_deleted
            ):
                # replace the following with your own logic for processing a file event
                return await self.process_workbench_file_event(assistant_instance.id, event.conversation_id, event)

            case _:
                pass

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

        # validate the assistant's configuration
        if not await self.validate_config(assistant_id, str(conversation_id)):
            return

        # get the assistant's configuration, supports overwriting defaults from environment variables
        assistant_config = self._config_storage.get_with_defaults_overwritten_from_env(assistant_id)

        # get the list of conversation participants
        participants_response = await conversation_client.get_participants(include_inactive=True)

        # establish a token to be used by the AI model to indicate no response
        silence_token = "{{SILENCE}}"

        # get assistant instance
        instance = self.assistant_instances.get(assistant_id)
        if instance is None:
            # unexpected, no instance
            # TODO log and handle error
            return

        client = self.workbench_client.for_conversation(assistant_id, str(conversation_id))

        messages = messages_response.messages

        system_message_content = f'{assistant_config.persona_prompt}\n\nYour name is "{instance.assistant_name}".'
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
                f' "{instance.assistant_name}". Sometimes the other users need to talk'
                " amongst themselves and that is ok. If the conversation seems to be directed at you or the general"
                f' audience, go ahead and respond.\n\nSay "{silence_token}" to skip your turn.'
            )

        completion_messages: list[chat.ChatCompletionMessageParam] = [{
            "role": "system",
            "content": system_message_content,
        }]

        current_tokens = 0
        current_tokens += self.get_token_count(system_message_content)  # add the system message tokens

        if assistant_config.agents_config.attachment_agent.include_in_response_generation:
            file_storage = self.get_file_storage_for_conversation(assistant_id, str(conversation_id))
            attachment_agent = AttachmentAgent(client, file_storage)
            attachment_messages = await attachment_agent.generate_attachment_messages()
            if len(attachment_messages) > 0:
                completion_messages.append({
                    "role": "system",
                    "content": assistant_config.agents_config.attachment_agent.context_description,
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
        for message in reversed(messages):
            message_tokens = self.get_token_count(format_message(message))
            current_tokens += message_tokens
            if (
                current_tokens
                > assistant_config.request_config.max_tokens - assistant_config.request_config.response_tokens
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
                if message.filenames and len(message.filenames) > 0:
                    history_messages.append({
                        "role": "system",
                        "content": f"User attached files: {', '.join(message.filenames)}",
                    })

        history_messages.reverse()
        completion_messages.extend(history_messages)
        total_tokens_from_completion: None | int = None

        async with self.get_openai_client(assistant_id) as openai_client:
            try:
                completion = await openai_client.chat.completions.create(
                    messages=completion_messages,
                    model=assistant_config.service_config.openai_model,
                    max_tokens=assistant_config.request_config.response_tokens,
                )
                content = completion.choices[0].message.content
                metadata = {
                    "debug": {
                        "response_generation": {
                            "request": {
                                "model": assistant_config.service_config.openai_model,
                                "messages": completion_messages,
                                "max_tokens": assistant_config.request_config.response_tokens,
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
                                "model": assistant_config.service_config.openai_model,
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
                if assistant_config.enable_debug_output:
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
        if total_tokens_from_completion is not None and assistant_config.high_token_usage_warning.enabled:
            token_count_for_warning = assistant_config.request_config.max_tokens * (
                assistant_config.high_token_usage_warning.threshold / 100
            )
            if total_tokens_from_completion > token_count_for_warning:
                await client.send_messages(
                    workbench_model.NewConversationMessage(
                        content=assistant_config.high_token_usage_warning.message,
                        message_type=workbench_model.MessageType.notice,
                    )
                )

    async def process_workbench_participant_created_event(
        self,
        assistant_id: str,
        conversation_id: UUID,
        event: workbench_model.ConversationEvent,
    ) -> None:
        # check if the participant is the assistant, if so send a welcome message
        if event.data.get("participant", {}).get("id") != assistant_id:
            # not the assistant, so ignore
            return

        client = self.workbench_client.for_conversation(assistant_id, str(conversation_id))
        assistant_config = self._config_storage.get_with_defaults_overwritten_from_env(assistant_id)

        # send a welcome message to the conversation
        await client.send_messages(
            workbench_model.NewConversationMessage(
                content=assistant_config.welcome_message,
                message_type=workbench_model.MessageType.chat,
                metadata={"debug": "welcome message from configuration"},
            )
        )

    async def process_workbench_file_event(
        self,
        assistant_id: str,
        conversation_id: UUID,
        event: workbench_model.ConversationEvent,
    ) -> None:
        client = self.workbench_client.for_conversation(assistant_id, str(conversation_id))
        file_storage = self.get_file_storage_for_conversation(assistant_id, str(conversation_id))
        attachment_agent = AttachmentAgent(client, file_storage)

        file_data = event.data.get("file")
        if file_data is None:
            logger.error("event is missing file")
            return
        file = workbench_model.File.model_validate(file_data)

        match event.event:

            case ConversationEventType.file_created | ConversationEventType.file_updated:
                await client.update_participant_me(
                    workbench_model.UpdateParticipant(
                        status="processing attachment...",
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

            case ConversationEventType.file_deleted:
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

    def get_openai_client(self, assistant_id: str) -> openai.AsyncOpenAI:
        assistant_config = self._config_storage.get_with_defaults_overwritten_from_env(assistant_id)
        return assistant_config.service_config.new_client()

    def get_token_count(self, string: str) -> int:
        encoding = tiktoken.get_encoding("cl100k_base")
        return len(encoding.encode(string))


app = assistant_service.create_app(
    lambda lifespan: ChatAssistant(
        register_lifespan_handler=lifespan.register_handler,
    )
)
