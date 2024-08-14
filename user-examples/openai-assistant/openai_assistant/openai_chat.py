import logging
import re
from typing import AsyncContextManager, Callable
from uuid import UUID

import openai
from openai.types.chat import ChatCompletionMessageParam
from semantic_workbench_api_model.workbench_model import (
    ConversationEvent,
    ConversationEventType,
    ConversationMessage,
    NewConversationMessage,
    MessageType,
    UpdateParticipant,
)
from semantic_workbench_assistant import assistant_service
from semantic_workbench_assistant.assistant_base import (
    AssistantBase,
    AssistantInstance,
    SimpleAssistantConfigStorage,
    AssistantConfigStorage,
)

import tiktoken

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

service_id = "openai-example.workbench-explorer"
service_name = "OpenAI Assistant"
service_description = "A sample OpenAI chat assistant using the Semantic Workbench Assistant SDK."


class ChatAssistant(AssistantBase):

    # Optional: override the __init__ method to add any additional initialization logic
    def __init__(
        self,
        register_lifespan_handler: Callable[[Callable[[], AsyncContextManager[None]]], None],
        service_id=service_id,
        service_name=service_name,
        service_description=service_description,
        config_storage: AssistantConfigStorage | None = None,
    ) -> None:

        super().__init__(
            register_lifespan_handler=register_lifespan_handler,
            service_id=service_id,
            service_name=service_name,
            service_description=service_description,
            config_storage=config_storage
            or SimpleAssistantConfigStorage[config.AssistantConfigModel](
                cls=config.AssistantConfigModel,
                default_config=config.AssistantConfigModel(),
                ui_schema=config.ui_schema,
            ),
        )

    # Custom: implement a custom method to validate the assistant's configurations
    async def validate_config(self, assistant_id: str, conversation_id: str) -> bool:
        assistant_config = self._config_storage.get_with_defaults_overwritten_from_env(assistant_id)
        valid, message_content = assistant_config.service_config.validate_required_fields()
        if valid:
            return True

        await self.workbench_client.for_conversation(assistant_id, conversation_id).send_messages(
            NewConversationMessage(content=message_content, message_type=MessageType.notice)
        )
        return False

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
        def format_message(message: ConversationMessage) -> str:
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

        history_messages.reverse()
        completion_messages.extend(history_messages)

        # Custom: add any additional logic for responding to a conversation
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

        message_type = MessageType.chat

        if content:
            # strip out the username from the response
            if content.startswith("["):
                content = re.sub(r"\[.*\]:\s", "", content)

            # model sometimes puts extra spaces in the response, so remove them
            # when checking for the silence token
            if content.replace(" ", "") == silence_token:
                if assistant_config.enable_debug_output:
                    await conversation_client.send_messages(
                        NewConversationMessage(
                            message_type=MessageType.notice,
                            content="[assistant chose to remain silent]",
                            metadata={"attribution": "debug output"},
                        )
                    )
                return

            # override message type if content starts with /
            if content.startswith("/"):
                message_type = MessageType.command_response

        await conversation_client.send_messages(
            NewConversationMessage(
                content=content or "[no response from openai]",
                message_type=message_type,
                metadata=metadata,
            )
        )

    def get_openai_client(self, assistant_id: str) -> openai.AsyncOpenAI:
        assistant_config = self._config_storage.get_with_defaults_overwritten_from_env(assistant_id)
        return assistant_config.service_config.new_client()

    def get_token_count(self, string: str) -> int:
        encoding = tiktoken.get_encoding("cl100k_base")
        return len(encoding.encode(string))


# Required: Create an instance of the Assistant class
app = assistant_service.create_app(
    lambda lifespan: ChatAssistant(
        register_lifespan_handler=lifespan.register_handler,
    )
)
