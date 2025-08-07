# Copyright (c) Microsoft. All rights reserved.

# An example for building a simple chat assistant using the AssistantApp from
# the semantic-workbench-assistant package.
#
# This example demonstrates how to use the AssistantApp to create a chat assistant,
# to add additional configuration fields and UI schema for the configuration fields,
# and to handle conversation events to respond to messages in the conversation.

# region Required
#
# The code in this region demonstrates the minimal code required to create a chat assistant
# using the AssistantApp class from the semantic-workbench-assistant package. This code
# demonstrates how to create an AssistantApp instance, define the service ID, name, and
# description, and create the FastAPI app instance. Start here to build your own chat
# assistant using the AssistantApp class.
#
# The code that follows this region is optional and demonstrates how to add event handlers
# to respond to conversation events. You can use this code as a starting point for building
# your own chat assistant with additional functionality.
#


import logging
import re
from typing import Any

import deepmerge
import openai_client
import tiktoken
from assistant_extensions.attachments import AttachmentsExtension
from content_safety.evaluators import CombinedContentSafetyEvaluator
from openai.types.chat import ChatCompletionMessageParam
from semantic_workbench_api_model.workbench_model import (
    ConversationEvent,
    ConversationMessage,
    MessageType,
    NewConversationMessage,
    UpdateParticipant,
)
from semantic_workbench_assistant.assistant_app import (
    AssistantApp,
    AssistantCapability,
    BaseModelAssistantConfig,
    ContentSafety,
    ContentSafetyEvaluator,
    ConversationContext,
)

from .config import AssistantConfigModel

logger = logging.getLogger(__name__)

#
# define the service ID, name, and description
#

# the service id to be registered in the workbench to identify the assistant
service_id = "python-02-simple-chatbot.workbench-explorer"
# the name of the assistant service, as it will appear in the workbench UI
service_name = "Python Example 02: Simple Chatbot"
# a description of the assistant service, as it will appear in the workbench UI
service_description = "A simple OpenAI chat assistant using the Semantic Workbench Assistant SDK."

#
# create the configuration provider, using the extended configuration model
#
assistant_config = BaseModelAssistantConfig(AssistantConfigModel)


# define the content safety evaluator factory
async def content_evaluator_factory(context: ConversationContext) -> ContentSafetyEvaluator:
    config = await assistant_config.get(context.assistant)
    return CombinedContentSafetyEvaluator(config.content_safety_config)


content_safety = ContentSafety(content_evaluator_factory)


# create the AssistantApp instance
assistant = AssistantApp(
    assistant_service_id=service_id,
    assistant_service_name=service_name,
    assistant_service_description=service_description,
    config_provider=assistant_config.provider,
    content_interceptor=content_safety,
)

# Add attachment support to enable file uploads
attachments_extension = AttachmentsExtension(assistant)

# File viewer that demonstrates the new backend API with flat listing and proper actions
class FileViewerStateProvider:
    def __init__(self):
        self.display_name = "📁 Files"
        self.description = "View uploaded files and processed content" 
        self.state_id = "file_viewer"
    
    async def is_enabled(self, context):
        """Only enabled when there are files"""
        files_response = await context.list_files()
        return len(files_response.files) > 0
    
    async def set(self, context, data):
        """Handle view processed content action"""
        selected_file = data.get("view_processed_file")
        if selected_file and selected_file != "__none__":
            await self._create_processed_content_viewer(context, selected_file)
    
    async def _create_processed_content_viewer(self, context, filename):
        """Create a dynamic canvas viewer tab showing processed content"""
        try:
            # Create a unique state provider for this file
            safe_filename = filename.replace('/', '_').replace(' ', '_').replace('.', '_')
            state_id = f"processed_content_{safe_filename}"
            
            # Check if already exists to avoid duplicates
            if hasattr(context, '_processed_viewers') and state_id in context._processed_viewers:
                return
                
            # Create the processed content provider
            provider = ProcessedContentViewerProvider(filename)
            
            # Register it dynamically with the assistant
            assistant.add_inspector_state_provider(state_id, provider)
            
            # Track it to avoid duplicates
            if not hasattr(context, '_processed_viewers'):
                context._processed_viewers = set()
            context._processed_viewers.add(state_id)
            
            # Send state event to notify frontend of new tab
            from semantic_workbench_api_model.workbench_model import AssistantStateEvent
            await context.send_conversation_state_event(
                AssistantStateEvent(
                    state_id=state_id,
                    event="created",
                    state=None
                )
            )
        except Exception as e:
            # Don't let errors break the form submission
            pass
    
    async def get(self, context):
        """Display file listing following Document Assistant pattern: downloads + action sections"""
        from semantic_workbench_assistant.assistant_app.protocol import AssistantConversationInspectorStateDataModel
        from assistant_extensions.attachments import get_attachments
        import io
        
        try:
            files_response = await context.list_files()
            
            if not files_response.files:
                return AssistantConversationInspectorStateDataModel(
                    data={"content": "No files uploaded yet."}
                )
            
            # Get processed data for all files using REAL API
            processed_data = {}
            try:
                attachments = await get_attachments(context, error_handler=attachments_extension._error_handler)
                for attachment in attachments:
                    if not attachment.error:
                        content_length = len(attachment.content)
                        line_count = attachment.content.count('\n') + 1 if content_length > 0 else 0
                        estimated_tokens = max(1, content_length // 4)
                        
                        processed_data[attachment.filename] = {
                            "success": True,
                            "character_count": content_length,
                            "line_count": line_count,
                            "estimated_tokens": estimated_tokens,
                        }
                    else:
                        processed_data[attachment.filename] = {
                            "success": False,
                            "error": attachment.error
                        }
            except Exception as e:
                # If processing fails, we still show downloads
                pass
            
            # Build attachments with actual file content for downloads
            attachments_list = []
            processed_files = []
            file_metadata = []  # Store metadata separately for display
            
            for file in files_response.files:
                try:
                    # Get actual file content for download
                    buffer = io.BytesIO()
                    async with context.read_file(file.filename) as reader:
                        async for chunk in reader:
                            buffer.write(chunk)
                    
                    file_content = buffer.getvalue()
                    
                    # Handle binary vs text files properly
                    if file.content_type.startswith('text/') or file.filename.endswith(('.txt', '.md', '.py', '.js', '.json', '.yaml', '.yml')):
                        # Text files - decode as UTF-8
                        content_str = file_content.decode("utf-8", errors="replace")
                    else:
                        # Binary files - create data URL with base64 encoding
                        import base64
                        encoded_content = base64.b64encode(file_content).decode('ascii')
                        content_str = f"data:{file.content_type};base64,{encoded_content}"
                    
                    # Add to attachments with proper content format
                    attachments_list.append({
                        "filename": file.filename,
                        "content": content_str
                    })
                    
                except Exception as e:
                    # If we can't read the file, skip it
                    continue
                
                # Create metadata for display
                size_mb = file.file_size / (1024 * 1024)
                size_str = f"{size_mb:.1f}MB" if size_mb >= 1.0 else f"{file.file_size:,} bytes"
                
                processed = processed_data.get(file.filename, {})
                status = "✅" if processed.get("success") else "❌" if file.filename in processed_data else "⏳"
                
                original_info = f"Original: {size_str} • {file.content_type}"
                if processed.get("success"):
                    processed_info = f"Processed: {processed['character_count']:,} chars • {processed['line_count']} lines • ~{processed['estimated_tokens']:,} tokens"
                else:
                    processed_info = f"Processing: {processed.get('error', 'In progress...')}"
                
                file_metadata.append(f"{status} {file.filename}\n   {original_info}\n   {processed_info}")
                
                # Track files available for processed content viewing
                if processed.get("success"):
                    processed_files.append(file.filename)
            
            # Build form data and schema with explicit ordering
            form_data = {}
            schema_props = {}
            ui_schema = {}
            
            # 1. Add downloads first (will appear at top)
            form_data["attachments"] = attachments_list
            
            # 2. Add file metadata display next (will be above processed content)
            if file_metadata:
                form_data["file_info"] = "\n\n".join(file_metadata)
                schema_props["file_info"] = {
                    "type": "string",
                    "title": "File Processing Information",
                    "readOnly": True
                }
                ui_schema["file_info"] = {
                    "ui:widget": "textarea",
                    "ui:options": {
                        "rows": len(file_metadata) + 1
                    }
                }
            
            # 3. Add processed content selection last (will be right above button)
            if processed_files:
                form_data["view_processed_file"] = "__none__"
                schema_props["view_processed_file"] = {
                    "type": "string", 
                    "title": "View Processed Content",
                    "enum": ["__none__"] + processed_files
                }
                ui_schema["view_processed_file"] = {
                    "ui:widget": "radio",
                    "ui:enumNames": ["Select a file..."] + [f"View {filename}" for filename in processed_files]
                }
            
            # Set submit button text and options
            if processed_files:
                ui_schema["ui:submitButtonOptions"] = {
                    "submitText": "View Selected File"
                }
            
            ui_schema["ui:options"] = {
                "collapsible": False,
                "hideTitle": False,
            }
            
            return AssistantConversationInspectorStateDataModel(
                data=form_data,
                json_schema={
                    "type": "object",
                    "properties": schema_props
                },
                ui_schema=ui_schema
            )
                
        except Exception as e:
            return AssistantConversationInspectorStateDataModel(
                data={"content": f"Error loading files: {str(e)}"}
            )

# Add the file viewer inspector
file_viewer_provider = FileViewerStateProvider()
assistant.add_inspector_state_provider("file_viewer", file_viewer_provider)

# Dynamic canvas viewer for processed content 
class ProcessedContentViewerProvider:
    """Creates dynamic canvas viewer tabs for processed file content"""
    
    def __init__(self, filename: str):
        self.filename = filename
        safe_filename = filename.replace('/', '_').replace(' ', '_').replace('.', '_')
        self.state_id = f"processed_content_{safe_filename}"
        self.display_name = f"📄 {filename}"
        self.description = f"Processed content from {filename}"
    
    async def is_enabled(self, context):
        return True  # Always available once created
    
    async def get(self, context):
        """Return processed content in appropriate viewer format"""
        from semantic_workbench_assistant.assistant_app.protocol import AssistantConversationInspectorStateDataModel
        from assistant_extensions.attachments import get_attachments
        
        try:
            # Get processed content via AttachmentsExtension  
            attachments = await get_attachments(context, error_handler=attachments_extension._error_handler)
            
            # Find the specific file
            attachment = next((a for a in attachments if a.filename == self.filename), None)
            
            if not attachment:
                return AssistantConversationInspectorStateDataModel(
                    data={"content": f"File '{self.filename}' not found in processed attachments"}
                )
            
            if attachment.error:
                return AssistantConversationInspectorStateDataModel(
                    data={"content": f"Error processing file: {attachment.error}"}
                )
            
            # Determine content type and return appropriate viewer format
            if attachment.content.startswith("data:image/"):
                # Image content - return as image data
                return AssistantConversationInspectorStateDataModel(
                    data={
                        "image": attachment.content,
                        "filename": self.filename
                    }
                )
            elif self.filename.endswith(('.md', '.markdown')):
                # Markdown content - use markdown viewer
                return AssistantConversationInspectorStateDataModel(
                    data={
                        "markdown_content": attachment.content,
                        "readonly": True
                    }
                )
            else:
                # Text/code content - use content viewer
                return AssistantConversationInspectorStateDataModel(
                    data={"content": attachment.content}
                )
            
        except Exception as e:
            return AssistantConversationInspectorStateDataModel(
                data={"content": f"Error retrieving processed content: {str(e)}"}
            )

#
# create the FastAPI app instance
#
app = assistant.fastapi_app()


# Track processed content state providers for dynamic creation
_file_content_providers = {}

@assistant.events.conversation.file.on_created
async def on_file_created(context: ConversationContext, event: ConversationEvent, file_info) -> None:
    """Create a processed content state provider when a file is uploaded"""
    global _file_content_providers
    
    filename = file_info.filename
    
    # Skip if we already have a provider for this file
    if filename in _file_content_providers:
        return
    
    # Create and register the processed content provider
    provider = ProcessedContentViewerProvider(filename)
    _file_content_providers[filename] = provider
    assistant.add_inspector_state_provider(provider.state_id, provider)


# endregion


# region Optional
#
# Note: The code in this region is specific to this example and is not required for a basic assistant.
#
# The AssistantApp class provides a set of decorators for adding event handlers to respond to conversation
# events. In VS Code, typing "@assistant." (or the name of your AssistantApp instance) will show available
# events and methods.
#
# See the semantic-workbench-assistant AssistantApp class for more information on available events and methods.
# Examples:
# - @assistant.events.conversation.on_created (event triggered when the assistant is added to a conversation)
# - @assistant.events.conversation.participant.on_created (event triggered when a participant is added)
# - @assistant.events.conversation.message.on_created (event triggered when a new message of any type is created)
# - @assistant.events.conversation.message.chat.on_created (event triggered when a new chat message is created)
#


@assistant.events.conversation.message.chat.on_created
async def on_message_created(
    context: ConversationContext, event: ConversationEvent, message: ConversationMessage
) -> None:
    """
    Handle the event triggered when a new chat message is created in the conversation.

    **Note**
    - This event handler is specific to chat messages.
    - To handle other message types, you can add additional event handlers for those message types.
      - @assistant.events.conversation.message.log.on_created
      - @assistant.events.conversation.message.command.on_created
      - ...additional message types
    - To handle all message types, you can use the root event handler for all message types:
      - @assistant.events.conversation.message.on_created
    """

    # update the participant status to indicate the assistant is thinking
    await context.update_participant_me(UpdateParticipant(status="thinking..."))
    try:
        # replace the following with your own logic for processing a message created event
        await respond_to_conversation(
            context,
            message=message,
            metadata={"debug": {"content_safety": event.data.get(content_safety.metadata_key, {})}},
        )
    finally:
        # update the participant status to indicate the assistant is done thinking
        await context.update_participant_me(UpdateParticipant(status=None))


# Handle the event triggered when the assistant is added to a conversation.
@assistant.events.conversation.on_created
async def on_conversation_created(context: ConversationContext) -> None:
    """
    Handle the event triggered when the assistant is added to a conversation.
    """
    # replace the following with your own logic for processing a conversation created event

    # get the assistant's configuration
    config = await assistant_config.get(context.assistant)

    # get the welcome message from the assistant's configuration
    welcome_message = config.welcome_message

    # send the welcome message to the conversation
    await context.send_messages(
        NewConversationMessage(
            content=welcome_message,
            message_type=MessageType.chat,
            metadata={"generated_content": False},
        )
    )


# endregion


# region Custom
#
# This code was added specifically for this example to demonstrate how to respond to conversation
# messages using the OpenAI API. For your own assistant, you could replace this code with your own
# logic for responding to conversation messages and add any additional functionality as needed.
#


# demonstrates how to respond to a conversation message using the OpenAI API.
async def respond_to_conversation(
    context: ConversationContext, message: ConversationMessage, metadata: dict[str, Any] = {}
) -> None:
    """
    Respond to a conversation message.
    """

    # define the metadata key for any metadata created within this method
    method_metadata_key = "respond_to_conversation"

    # get the assistant's configuration, supports overwriting defaults from environment variables
    config = await assistant_config.get(context.assistant)

    # get the list of conversation participants
    participants_response = await context.get_participants(include_inactive=True)

    # establish a token to be used by the AI model to indicate no response
    silence_token = "{{SILENCE}}"

    # create a system message, start by adding the guardrails prompt
    system_message_content = config.guardrails_prompt

    # add the instruction prompt and the assistant name
    system_message_content += f'\n\n{config.instruction_prompt}\n\nYour name is "{context.assistant.name}".'

    # if this is a multi-participant conversation, add a note about the participants
    if len(participants_response.participants) > 2:
        system_message_content += (
            "\n\n"
            f"There are {len(participants_response.participants)} participants in the conversation,"
            " including you as the assistant and the following users:"
            + ",".join([
                f' "{participant.name}"'
                for participant in participants_response.participants
                if participant.id != context.assistant.id
            ])
            + "\n\nYou do not need to respond to every message. Do not respond if the last thing said was a closing"
            " statement such as 'bye' or 'goodbye', or just a general acknowledgement like 'ok' or 'thanks'. Do not"
            f' respond as another user in the conversation, only as "{context.assistant.name}".'
            " Sometimes the other users need to talk amongst themselves and that is ok. If the conversation seems to"
            f' be directed at you or the general audience, go ahead and respond.\n\nSay "{silence_token}" to skip'
            " your turn."
        )

    # create the completion messages for the AI model and add the system message
    completion_messages: list[ChatCompletionMessageParam] = [
        {
            "role": "system",
            "content": system_message_content,
        }
    ]

    # get the current token count and track the tokens used as messages are added
    current_tokens = 0
    # add the token count for the system message
    current_tokens += get_token_count(system_message_content)

    # consistent formatter that includes the participant name for multi-participant and name references
    def format_message(message: ConversationMessage) -> str:
        # get the participant name for the message sender
        conversation_participant = next(
            (
                participant
                for participant in participants_response.participants
                if participant.id == message.sender.participant_id
            ),
            None,
        )
        participant_name = conversation_participant.name if conversation_participant else "unknown"

        # format the message content with the participant name and message timestamp
        message_datetime = message.timestamp.strftime("%Y-%m-%d %H:%M:%S")
        return f"[{participant_name} - {message_datetime}]: {message.content}"

    # get messages before the current message
    messages_response = await context.get_messages(before=message.id)
    messages = messages_response.messages + [message]

    # create a list of the recent chat history messages to send to the AI model
    history_messages: list[ChatCompletionMessageParam] = []
    # iterate over the messages in reverse order to get the most recent messages first
    for message in reversed(messages):
        # add the token count for the message and check if the token limit has been reached
        message_tokens = get_token_count(format_message(message))
        current_tokens += message_tokens
        if current_tokens > config.request_config.max_tokens - config.request_config.response_tokens:
            # if the token limit has been reached, stop adding messages
            break

        # add the message to the history messages
        if message.sender.participant_id == context.assistant.id:
            # this is an assistant message
            history_messages.append({
                "role": "assistant",
                "content": format_message(message),
            })
        else:
            # this is a user message
            history_messages.append({
                "role": "user",
                "content": format_message(message),
            })

    # reverse the history messages to send the most recent messages first
    history_messages.reverse()

    # add the history messages to the completion messages
    completion_messages.extend(history_messages)

    # evaluate the content for safety
    # disabled because the OpenAI and Azure OpenAI services already have content safety checks
    # and we are more interested in running the generated responses through the content safety checks
    # which are being handled by the content safety interceptor on the assistant
    # this code is therefore included here for reference on how to call the content safety evaluator
    # from within the assistant code

    # content_evaluator = await content_evaluator_factory(context)
    # evaluation = await content_evaluator.evaluate([message.content for message in messages])

    # deepmerge.always_merger.merge(
    #     metadata,
    #     {
    #         "debug": {
    #             f"{assistant.content_interceptor.metadata_key}": {
    #                 f"{method_metadata_key}": {
    #                     "evaluation": evaluation.model_dump(),
    #                 },
    #             },
    #         },
    #     },
    # )

    # if evaluation.result == ContentSafetyEvaluationResult.Fail:
    #     # send a notice to the user that the content safety evaluation failed
    #     deepmerge.always_merger.merge(
    #         metadata,
    #         {"generated_content": False},
    #     )
    #     await context.send_messages(
    #         NewConversationMessage(
    #             content=evaluation.note or "Content safety evaluation failed.",
    #             message_type=MessageType.notice,
    #             metadata=metadata,
    #         )
    #     )
    #     return

    # generate a response from the AI model
    async with openai_client.create_client(config.service_config, api_version="2024-06-01") as client:
        try:
            # call the OpenAI chat completion endpoint to get a response
            completion = await client.chat.completions.create(
                messages=completion_messages,
                model=config.request_config.openai_model,
                max_tokens=config.request_config.response_tokens,
            )

            # get the content from the completion response
            content = completion.choices[0].message.content

            # merge the completion response into the passed in metadata
            deepmerge.always_merger.merge(
                metadata,
                {
                    "debug": {
                        f"{method_metadata_key}": {
                            "request": {
                                "model": config.request_config.openai_model,
                                "messages": completion_messages,
                                "max_tokens": config.request_config.response_tokens,
                            },
                            "response": completion.model_dump() if completion else "[no response from openai]",
                        },
                    }
                },
            )
        except Exception as e:
            logger.exception(f"exception occurred calling openai chat completion: {e}")
            # if there is an error, set the content to an error message
            content = "An error occurred while calling the OpenAI API. Is it configured correctly?"

            # merge the error into the passed in metadata
            deepmerge.always_merger.merge(
                metadata,
                {
                    "debug": {
                        f"{method_metadata_key}": {
                            "request": {
                                "model": config.request_config.openai_model,
                                "messages": completion_messages,
                            },
                            "error": str(e),
                        },
                    }
                },
            )

    # set the message type based on the content
    message_type = MessageType.chat

    # various behaviors based on the content
    if content:
        # strip out the username from the response
        if content.startswith("["):
            content = re.sub(r"\[.*\]:\s", "", content)

        # check for the silence token, in case the model chooses not to respond
        # model sometimes puts extra spaces in the response, so remove them
        # when checking for the silence token
        if content.replace(" ", "") == silence_token:
            # normal behavior is to not respond if the model chooses to remain silent
            # but we can override this behavior for debugging purposes via the assistant config
            if config.enable_debug_output:
                # update the metadata to indicate the assistant chose to remain silent
                deepmerge.always_merger.merge(
                    metadata,
                    {
                        "debug": {
                            f"{method_metadata_key}": {
                                "silence_token": True,
                            },
                        },
                        "attribution": "debug output",
                        "generated_content": False,
                    },
                )
                # send a notice to the user that the assistant chose to remain silent
                await context.send_messages(
                    NewConversationMessage(
                        message_type=MessageType.notice,
                        content="[assistant chose to remain silent]",
                        metadata=metadata,
                    )
                )
            return

        # override message type if content starts with "/", indicating a command response
        if content.startswith("/"):
            message_type = MessageType.command_response

    # send the response to the conversation
    await context.send_messages(
        NewConversationMessage(
            content=content or "[no response from openai]",
            message_type=message_type,
            metadata=metadata,
        )
    )


# this method is used to get the token count of a string.
def get_token_count(string: str) -> int:
    """
    Get the token count of a string.
    """
    encoding = tiktoken.get_encoding("cl100k_base")
    return len(encoding.encode(string))


# endregion
