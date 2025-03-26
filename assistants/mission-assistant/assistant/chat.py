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
from content_safety.evaluators import CombinedContentSafetyEvaluator
from openai.types.chat import ChatCompletionMessageParam
from semantic_workbench_api_model import workbench_model
from semantic_workbench_api_model.workbench_model import (
    AssistantStateEvent,
    ConversationEvent,
    ConversationMessage,
    MessageType,
    NewConversationMessage,
    UpdateParticipant,
)
from semantic_workbench_assistant.assistant_app import (
    AssistantApp,
    BaseModelAssistantConfig,
    ContentSafety,
    ContentSafetyEvaluator,
    ConversationContext,
)

from .artifact_messaging import ArtifactMessenger
from .config import AssistantConfigModel
from .mission import FileSynchronizer, MissionManager, MissionStateManager
from .state_inspector import MissionInspectorStateProvider

logger = logging.getLogger(__name__)

#
# define the service ID, name, and description
#

# the service id to be registered in the workbench to identify the assistant
service_id = "mission-assistant.workbench-explorer"
# the name of the assistant service, as it will appear in the workbench UI
service_name = "Mission Assistant"
# a description of the assistant service, as it will appear in the workbench UI
service_description = "A mediator assistant that facilitates file sharing between conversations."

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
    inspector_state_providers={
        "mission_status": MissionInspectorStateProvider(assistant_config),
    },
)

#
# create the FastAPI app instance
#
app = assistant.fastapi_app()


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
        # Get the conversation's role (HQ or Field)
        # Get conversation to access metadata
        conversation = await context.get_conversation()
        metadata = conversation.metadata or {}
        role = metadata.get("mission_role")

        # If role isn't set yet, detect it now
        if not role:
            role = await detect_assistant_role(context)
            metadata["mission_role"] = role
            # Update conversation metadata through appropriate method
            await context.send_conversation_state_event(
                AssistantStateEvent(
                    state_id="mission_role",
                    event="updated",
                    state=None
                )
            )

        # Prepare custom system message based on role
        role_specific_prompt = ""

        if role == "hq":
            # HQ-specific instructions
            role_specific_prompt = """
You are operating in HQ Mode (Definition Stage). Your responsibilities include:
- Creating a clear Mission Briefing that outlines the mission's purpose and objectives
- Defining specific, actionable mission goals that field personnel will need to complete
- Establishing measurable success criteria for each goal to track field progress
- Building a comprehensive Mission Knowledge Base with mission-critical information
- Providing guidance and information to field personnel
- Responding to Field Requests from mission participants
- Controlling the "Ready for Field" gate when mission definition is complete
- Maintaining an overview of mission progress

IMPORTANT: Mission goals are operational objectives for field personnel to complete, not goals for HQ. 
Each goal should:
- Be clear and specific tasks that field personnel need to accomplish
- Include measurable success criteria that field personnel can mark as completed
- Focus on mission outcomes, not the planning process

You have access to the following HQ-specific tools that you MUST use to manage mission artifacts:
- create_mission_briefing: Use this to start a new mission with a name and description
- add_mission_goal: Use this to add operational goals that field personnel will complete, with measurable success criteria
- add_kb_section: Use this to add information sections to the mission knowledge base for field reference
- resolve_field_request: Use this to resolve information requests or blockers reported by field personnel
- mark_mission_ready_for_field: Use this when mission planning is complete and field operations can begin
- get_mission_info: Use this to get information about the current mission

Be proactive in suggesting and using these tools based on user requests. Always prefer using tools over just discussing mission concepts.

Use a strategic, guidance-oriented tone focused on mission definition and support.
"""
        else:
            # Field-specific instructions
            role_specific_prompt = """
You are operating in Field Mode (Working Stage). Your responsibilities include:
- Helping field personnel understand and execute the mission objectives defined by HQ
- Providing access to the Mission Knowledge Base created by HQ
- Guiding field personnel to complete the mission goals established by HQ
- Tracking and marking completion of success criteria for each goal
- Logging information gaps and blockers as Field Requests to HQ
- Updating Mission Status with progress on operational tasks
- Tracking progress toward the "Mission Completion" gate

IMPORTANT: Your role is to help field personnel accomplish the mission goals that were defined by HQ. 
You should:
- Focus on executing the goals, not redefining them
- Mark success criteria as completed when field personnel report completion
- Identify information gaps or blockers that require HQ assistance

You have access to the following Field-specific tools that you MUST use to manage mission execution:
- create_field_request: Use this to create requests for information or report blockers to HQ
- update_mission_status: Use this to update the status and progress of the mission
- mark_criterion_completed: Use this to mark success criteria as completed
- report_mission_completion: Use this to report that the mission is complete
- detect_field_request_needs: Use this to analyze messages for potential field request needs
- get_mission_info: Use this to get information about the current mission

Be proactive in suggesting and using these tools based on user requests. Always prefer using tools over just discussing mission concepts.

Use a practical, operational tone focused on mission execution and problem-solving.
"""

        # Add role-specific metadata to pass to the LLM
        role_metadata = {
            "mission_role": role,
            "role_description": "HQ Mode (Definition Stage)" if role == "hq" else "Field Mode (Working Stage)",
            "debug": {"content_safety": event.data.get(content_safety.metadata_key, {})},
        }

        # respond to the message with role-specific context
        await respond_to_conversation(
            context, message=message, metadata=role_metadata, role_specific_prompt=role_specific_prompt
        )
    finally:
        # update the participant status to indicate the assistant is done thinking
        await context.update_participant_me(UpdateParticipant(status=None))


@assistant.events.conversation.message.command.on_created
async def on_command_created(
    context: ConversationContext, event: ConversationEvent, message: ConversationMessage
) -> None:
    """
    Handle command messages using the centralized command processor.
    """
    # update the participant status to indicate the assistant is thinking
    await context.update_participant_me(UpdateParticipant(status="processing command..."))
    try:
        # Get the conversation's role (HQ or Field)
        conversation = await context.get_conversation()
        metadata = conversation.metadata or {}
        role = metadata.get("mission_role")

        # If role isn't set yet, detect it now
        if not role:
            role = await detect_assistant_role(context)
            metadata["mission_role"] = role
            await context.send_conversation_state_event(
                AssistantStateEvent(
                    state_id="mission_role",
                    event="updated",
                    state=None
                )
            )
        
        # Process the command using the command processor
        from .command_processor import process_command
        command_processed = await process_command(context, message)
        
        # If the command wasn't recognized or processed, respond normally
        if not command_processed:
            await respond_to_conversation(
                context,
                message=message,
                metadata={"debug": {"content_safety": event.data.get(content_safety.metadata_key, {})}},
            )
    finally:
        # update the participant status to indicate the assistant is done thinking
        await context.update_participant_me(UpdateParticipant(status=None))


@assistant.events.conversation.file.on_created
async def on_file_created(context: ConversationContext, event: workbench_model.ConversationEvent, file: workbench_model.File) -> None:
    """
    Handle when a file is created in the conversation, sync to linked conversations if needed.
    """
    try:
        # Get config to check if auto-sync is enabled
        config = await assistant_config.get(context.assistant)
        if not config.mission_config.auto_sync_files:
            return

        # Get the file name from the File object
        filename = file.filename
        if not filename:
            return

        # Check if file should be synced to other conversations
        target_conversations = await MissionManager.should_sync_file(context, filename)
        if not target_conversations:
            return

        # Notify about file synchronization
        await context.send_messages(
            NewConversationMessage(
                content=f"File '{filename}' has been synchronized with {len(target_conversations)} linked conversation(s).",
                message_type=MessageType.notice,
            )
        )

        # In a real implementation, synchronize files to target conversations
        for target_id in target_conversations:
            await FileSynchronizer.sync_file(context, target_id, filename)

    except Exception as e:
        logger.exception(f"Error handling file creation: {e}")


@assistant.events.conversation.file.on_updated
async def on_file_updated(context: ConversationContext, event: workbench_model.ConversationEvent, file: workbench_model.File) -> None:
    """
    Handle when a file is updated in the conversation, sync updates to linked conversations.
    """
    try:
        # Identical logic to on_file_created, could be refactored to a common method
        # Get config to check if auto-sync is enabled
        config = await assistant_config.get(context.assistant)
        if not config.mission_config.auto_sync_files:
            return

        # Get the file name from the File object
        filename = file.filename
        if not filename:
            return

        # Check if file should be synced to other conversations
        target_conversations = await MissionManager.should_sync_file(context, filename)
        if not target_conversations:
            return

        # Notify about file synchronization
        await context.send_messages(
            NewConversationMessage(
                content=f"Updated file '{filename}' has been synchronized with {len(target_conversations)} linked conversation(s).",
                message_type=MessageType.notice,
            )
        )

        # In a real implementation, synchronize files to target conversations
        for target_id in target_conversations:
            await FileSynchronizer.sync_file(context, target_id, filename)

    except Exception as e:
        logger.exception(f"Error handling file update: {e}")


# Handle artifact messages (sent between conversations)
@assistant.events.conversation.message.notice.on_created
async def on_notice_created(
    context: ConversationContext, event: ConversationEvent, message: ConversationMessage
) -> None:
    """
    Handle notice messages, which may contain artifact data.
    """
    metadata = message.metadata or {}

    # Check if this is an artifact message
    if "artifact_message" in metadata:
        # Process the artifact message
        await ArtifactMessenger.process_artifact_message(context, message)
        return

    # Check if this is an artifact request
    if "artifact_request" in metadata:
        # Process the artifact request
        await ArtifactMessenger.process_artifact_request(context, message)
        return


# Role detection for the mission assistant
async def detect_assistant_role(context: ConversationContext) -> str:
    """
    Detects whether this conversation is in HQ Mode or Field Mode.

    Returns:
        "hq" if in HQ Mode, "field" if in Field Mode
    """
    try:
        # Check if this conversation has an active invitation from another conversation
        links = await MissionStateManager.get_links(context)

        # If we have linked to conversations but didn't create a briefing,
        # we're likely in Field Mode
        if links.linked_conversations:
            # Check if this conversation created a mission briefing
            from .artifacts import MissionBriefing
            briefings = await ArtifactMessenger.get_artifacts_by_type(context, MissionBriefing)

            # If we have briefings that were created by this conversation, we're in HQ Mode
            for briefing in briefings:
                if briefing.conversation_id == str(context.id):
                    return "hq"

            # If we have links to other conversations and didn't create the briefing,
            # we're in Field Mode
            for conv_id, linked_conv in links.linked_conversations.items():
                if conv_id != str(context.id):
                    return "field"

        # Default to HQ Mode for new conversations
        return "hq"

    except Exception as e:
        logger.exception(f"Error detecting assistant role: {e}")
        # Default to HQ Mode if detection fails
        return "hq"


# Handle the event triggered when the assistant is added to a conversation.
@assistant.events.conversation.on_created
async def on_conversation_created(context: ConversationContext) -> None:
    """
    Handle the event triggered when the assistant is added to a conversation.
    """
    # get the assistant's configuration
    config = await assistant_config.get(context.assistant)

    # Detect whether this is an HQ or Field conversation
    role = await detect_assistant_role(context)

    # Store the role in conversation metadata for future reference
    conversation = await context.get_conversation()
    metadata = conversation.metadata or {}
    metadata["mission_role"] = role
    await context.send_conversation_state_event(
        AssistantStateEvent(
            state_id="mission_role",
            event="updated",
            state=None
        )
    )

    # Select the appropriate welcome message based on role
    if role == "hq":
        welcome_message = config.mission_config.sender_config.welcome_message
    else:
        welcome_message = config.mission_config.receiver_config.welcome_message

    # send the welcome message to the conversation
    await context.send_messages(
        NewConversationMessage(
            content=welcome_message,
            message_type=MessageType.chat,
            metadata={"generated_content": False},
        )
    )

    # If this is an HQ conversation and proactive guidance is enabled,
    # provide guidance on getting started
    if role == "hq" and config.mission_config.proactive_guidance:
        await context.send_messages(
            NewConversationMessage(
                content=config.mission_config.sender_config.prompt_for_files,
                message_type=MessageType.chat,
            )
        )


# The command handling functions have been moved to command_processor.py


# endregion


# region Custom
#
# This code was added specifically for this example to demonstrate how to respond to conversation
# messages using the OpenAI API. For your own assistant, you could replace this code with your own
# logic for responding to conversation messages and add any additional functionality as needed.
#


# demonstrates how to respond to a conversation message using the OpenAI API.
async def respond_to_conversation(
    context: ConversationContext,
    message: ConversationMessage,
    metadata: dict[str, Any] = {},
    role_specific_prompt: str = "",
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

    # Add role-specific instructions if provided
    if role_specific_prompt:
        system_message_content += f"\n\n{role_specific_prompt}"

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

    # Get the conversation's role
    from .mission_tools import get_mission_tools, MissionTools

    conversation = await context.get_conversation()
    metadata = conversation.metadata or {}
    role = metadata.get("mission_role", "hq")  # Default to HQ if not set

    # For field role, analyze message for possible field request needs
    if role == "field" and message.message_type == MessageType.chat:
        # Create a mission tools instance for field role
        mission_tools_instance = MissionTools(context, role)
        
        # Check if the message indicates a potential field request
        detection_result = await mission_tools_instance.detect_field_request_needs(message.content)
        
        # If a field request is detected, suggest creating one
        if detection_result.get("is_field_request", False):
            # Get potential title and priority from detection
            suggested_title = detection_result.get("potential_title", "")
            suggested_priority = detection_result.get("suggested_priority", "medium")
            
            suggestion = (
                f"It sounds like you might need information from HQ. "
                f"Would you like me to create a field request titled '{suggested_title}' with {suggested_priority} priority?"
            )
            
            await context.send_messages(
                NewConversationMessage(
                    content=suggestion,
                    message_type=MessageType.notice,
                )
            )

    # Set up mission tools for the completion based on role
    mission_tools = await get_mission_tools(context, role)

    # Generate a response from the AI model with tools
    async with openai_client.create_client(config.service_config, api_version="2024-06-01") as client:
        try:
            # Create a completion dictionary for tool call handling
            completion_args = {
                "messages": completion_messages,
                "model": config.request_config.openai_model,
                "max_tokens": config.request_config.response_tokens,
            }

            # If the messaging API version supports tool functions, use them
            try:
                from openai_client.tools import complete_with_tool_calls

                # Call the completion API with tool functions
                logger.info("Using tool functions for completions")

                tool_completion, tool_messages = await complete_with_tool_calls(
                    async_client=client,
                    completion_args=completion_args,
                    tool_functions=mission_tools.tool_functions,
                    metadata=metadata,
                )

                # Get the final assistant message content
                content = None
                for msg in tool_messages:
                    if msg["role"] == "assistant" and "content" in msg and msg["content"]:
                        content = msg["content"]

                if not content:
                    # Fallback if no final message was generated
                    content = "I've processed your request, but couldn't generate a proper response."

                # Add tool call message exchange to metadata for debugging
                deepmerge.always_merger.merge(
                    metadata,
                    {
                        "debug": {
                            f"{method_metadata_key}": {
                                "tool_messages": str(tool_messages),
                                "response": tool_completion.model_dump()
                                if tool_completion
                                else "[no response from openai]",
                            },
                        }
                    },
                )

            except (ImportError, AttributeError):
                # Fallback to standard completions if tool calls aren't supported
                logger.info("Tool functions not supported, falling back to standard completion")

                # Call the OpenAI chat completion endpoint to get a response
                completion = await client.chat.completions.create(**completion_args)

                # Get the content from the completion response
                content = completion.choices[0].message.content

                # Merge the completion response into the passed in metadata
                deepmerge.always_merger.merge(
                    metadata,
                    {
                        "debug": {
                            f"{method_metadata_key}": {
                                "request": completion_args,
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
        if isinstance(content, str) and content.startswith("["):
            content = re.sub(r"\[.*\]:\s", "", content)

        # check for the silence token, in case the model chooses not to respond
        # model sometimes puts extra spaces in the response, so remove them
        # when checking for the silence token
        if isinstance(content, str) and content.replace(" ", "") == silence_token:
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
        if isinstance(content, str) and content.startswith("/"):
            message_type = MessageType.command_response

    # send the response to the conversation
    await context.send_messages(
        NewConversationMessage(
            content=str(content) if content is not None else "[no response from openai]",
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
