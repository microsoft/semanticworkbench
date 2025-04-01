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
    ParticipantRole,
    UpdateParticipant,
)
from semantic_workbench_assistant.assistant_app import (
    AssistantApp,
    BaseModelAssistantConfig,
    ContentSafety,
    ContentSafetyEvaluator,
    ConversationContext,
)

from .config import AssistantConfigModel
from .mission import MissionManager
from .mission_storage import MissionStorage, ConversationMissionManager
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
        # Get conversation to access metadata
        conversation = await context.get_conversation()
        metadata = conversation.metadata or {}
        
        # Check if setup is complete - check both local metadata and the state API
        setup_complete = metadata.get("setup_complete", False)
        
        # If not set in local metadata, try to get it from the mission storage directly
        if not setup_complete:
            try:
                from .mission_storage import ConversationMissionManager
                
                # Check if we have a mission role in storage
                role = await ConversationMissionManager.get_conversation_role(context)
                if role:
                    # If we have a role in storage, consider setup complete
                    setup_complete = True
                    metadata["setup_complete"] = True
                    metadata["mission_role"] = role.value
                    metadata["assistant_mode"] = role.value
                    logger.info(f"Found mission role in storage: {role.value}")
            except Exception as e:
                logger.exception(f"Error getting role from mission storage: {e}")
                
        assistant_mode = metadata.get("assistant_mode", "setup")
        
        # If setup isn't complete, show setup required message
        if not setup_complete and assistant_mode == "setup":
            # Show setup required message for regular chat messages
            await context.send_messages(
                NewConversationMessage(
                    content=(
                        "**Setup Required**\n\n"
                        "You need to set up the assistant before proceeding. Please use one of these commands:\n\n"
                        "- `/start-hq` - Create a new mission as HQ\n"
                        "- `/join <code>` - Join an existing mission as a Field agent\n"
                        "- `/help` - Get help with available commands"
                    ),
                    message_type=MessageType.notice,
                )
            )
            return
            
        # Get the conversation's role (HQ or Field)
        role = metadata.get("mission_role")

        # If role isn't set yet, detect it now
        if not role:
            role = await detect_assistant_role(context)
            metadata["mission_role"] = role
            # Update conversation metadata through appropriate method
            await context.send_conversation_state_event(
                AssistantStateEvent(state_id="mission_role", event="updated", state=None)
            )

        # If this is an HQ conversation, store the message for Field access
        if role == "hq" and message.message_type == MessageType.chat:
            try:
                # Get the mission ID
                from .mission_manager import MissionManager

                mission_id = await MissionManager.get_mission_id(context)

                if mission_id:
                    # Get the sender's name
                    sender_name = "HQ"
                    if message.sender:
                        participants = await context.get_participants()
                        for participant in participants.participants:
                            if participant.id == message.sender.participant_id:
                                sender_name = participant.name
                                break

                    # Store the message for Field access
                    from .mission_storage import MissionStorage

                    MissionStorage.append_hq_message(
                        mission_id=mission_id,
                        message_id=str(message.id),
                        content=message.content,
                        sender_name=sender_name,
                        is_assistant=message.sender.participant_role == ParticipantRole.assistant,
                        timestamp=message.timestamp,
                    )
                    logger.info(f"Stored HQ message for Field access: {message.id}")
            except Exception as e:
                # Don't fail message handling if storage fails
                logger.exception(f"Error storing HQ message for Field access: {e}")

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
- Responding to Field Requests from mission participants (using get_mission_info first to get the correct Request ID)
- Controlling the "Ready for Field" gate when mission definition is complete
- Maintaining an overview of mission progress

IMPORTANT: Mission goals are operational objectives for field personnel to complete, not goals for HQ.
Each goal should:
- Be clear and specific tasks that field personnel need to accomplish
- Include measurable success criteria that field personnel can mark as completed
- Focus on mission outcomes, not the planning process

Your AUTHORIZED HQ-specific tools are:
- create_mission_briefing: Use this to start a new mission with a name and description
- add_mission_goal: Use this to add operational goals that field personnel will complete, with measurable success criteria
- add_kb_section: Use this to add information sections to the mission knowledge base for field reference
- resolve_field_request: Use this to resolve field requests. VERY IMPORTANT: You MUST use get_mission_info first to get the actual request ID (looks like "abc123-def-456"), and then use that exact ID in the request_id parameter, NOT the title of the request.
- mark_mission_ready_for_field: Use this when mission planning is complete and field operations can begin
- get_mission_info: Use this to get information about the current mission
- suggest_next_action: Use this to suggest the next action based on mission state

⚠️ CRITICAL INSTRUCTION: You are an HQ agent and do NOT have access to Field tools. You will receive an ERROR if you try to use these Field-only tools:
- create_field_request: ❌ FORBIDDEN - Only Field can create field requests
- update_mission_status: ❌ FORBIDDEN - Only Field can update mission status
- mark_criterion_completed: ❌ FORBIDDEN - Only Field can mark criteria as completed
- report_mission_completion: ❌ FORBIDDEN - Only Field can report mission completion
- detect_field_request_needs: ❌ FORBIDDEN - Only Field can detect request needs

Be proactive in suggesting and using your HQ tools based on user requests. Always prefer using tools over just discussing mission concepts. If field personnel need to perform a task, instruct them to switch to their Field conversation.

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

Your AUTHORIZED Field-specific tools are:
- create_field_request: Use this SPECIFICALLY to send information requests or report blockers to HQ
- update_mission_status: Use this to update the status and progress of the mission
- mark_criterion_completed: Use this to mark success criteria as completed
- report_mission_completion: Use this to report that the mission is complete
- get_mission_info: Use this to get information about the current mission
- detect_field_request_needs: Use this to analyze user messages for potential field request needs
- suggest_next_action: Use this to suggest the next action based on mission state

⚠️ CRITICAL INSTRUCTION: You are a FIELD agent and do NOT have access to HQ tools. You will receive an ERROR if you try to use these HQ-only tools:
- resolve_field_request: ❌ FORBIDDEN - Use create_field_request instead to ask HQ for information
- create_mission_briefing: ❌ FORBIDDEN - Only HQ can create mission briefings
- add_mission_goal: ❌ FORBIDDEN - Only HQ can define mission goals
- add_kb_section: ❌ FORBIDDEN - Only HQ can add to the knowledge base
- mark_mission_ready_for_field: ❌ FORBIDDEN - Only HQ controls this gate

When field personnel need information or assistance from HQ:
1. ALWAYS use the create_field_request tool
2. NEVER try to use HQ-only tools like resolve_field_request
3. NEVER try to modify mission definition elements (briefing, goals, KB)
4. TELL THE USER you're creating a field request to get HQ assistance

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
                AssistantStateEvent(state_id="mission_role", event="updated", state=None)
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
async def on_file_created(
    context: ConversationContext, event: workbench_model.ConversationEvent, file: workbench_model.File
) -> None:
    """
    Handle when a file is created in the conversation.
    Files are stored in the shared mission directory and don't need explicit syncing.
    """
    try:
        # Get mission ID
        mission_id = await MissionManager.get_mission_id(context)
        if not mission_id or not file.filename:
            return

        # Log file creation to mission log
        await MissionStorage.log_mission_event(
            context=context,
            mission_id=mission_id,
            entry_type="file_shared",
            message=f"File shared: {file.filename}",
        )

    except Exception as e:
        logger.exception(f"Error handling file creation: {e}")


@assistant.events.conversation.file.on_updated
async def on_file_updated(
    context: ConversationContext, event: workbench_model.ConversationEvent, file: workbench_model.File
) -> None:
    """
    Handle when a file is updated in the conversation.
    Files are stored in the shared mission directory and don't need explicit syncing.
    """
    try:
        # Get mission ID
        mission_id = await MissionManager.get_mission_id(context)
        if not mission_id or not file.filename:
            return

        # Log file update to mission log
        await MissionStorage.log_mission_event(
            context=context,
            mission_id=mission_id,
            entry_type="file_shared",
            message=f"File updated: {file.filename}",
        )

    except Exception as e:
        logger.exception(f"Error handling file update: {e}")


# Notice messages are now simpler without artifact abstraction
@assistant.events.conversation.message.notice.on_created
async def on_notice_created(
    context: ConversationContext, event: ConversationEvent, message: ConversationMessage
) -> None:
    """
    Handle notice messages.
    """
    # No special handling needed now that we've removed artifact messaging
    pass


# Role detection for the mission assistant
async def detect_assistant_role(context: ConversationContext) -> str:
    """
    Detects whether this conversation is in HQ Mode or Field Mode.

    Returns:
        "hq" if in HQ Mode, "field" if in Field Mode
    """
    try:
        # First check if there's already a role set in mission storage
        role = await ConversationMissionManager.get_conversation_role(context)
        if role:
            return role.value

        # Get mission ID
        mission_id = await MissionManager.get_mission_id(context)
        if not mission_id:
            # No mission association yet, default to HQ
            return "hq"

        # Check if this conversation created a mission briefing
        briefing = MissionStorage.read_mission_briefing(mission_id)

        # If the briefing was created by this conversation, we're in HQ Mode
        if briefing and briefing.conversation_id == str(context.id):
            return "hq"

        # Otherwise, if we have a mission association but didn't create the briefing,
        # we're likely in Field Mode
        return "field"

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
    # Get conversation to access metadata
    conversation = await context.get_conversation()
    metadata = conversation.metadata or {}

    # Set initial setup mode for new conversations
    metadata["setup_complete"] = False
    metadata["assistant_mode"] = "setup"

    # Detect whether this is an HQ or Field conversation based on existing data
    # but don't commit to a role yet - that will happen during setup
    role = await detect_assistant_role(context)

    # Store the preliminary role in conversation metadata, but setup is not complete
    metadata["mission_role"] = role

    # Update conversation metadata
    await context.send_conversation_state_event(
        AssistantStateEvent(state_id="mission_role", event="updated", state=None)
    )

    # Welcome message for setup mode
    setup_welcome = """# Welcome to the Mission Assistant

This assistant helps coordinate mission activities between HQ and Field personnel.

**Setup Required**: To begin, please specify your role:

- Use `/start-hq` to create a new mission as HQ
- Use `/join <code>` to join an existing mission as Field personnel

Type `/help` for more information on available commands.
"""

    # send the setup welcome message to the conversation
    await context.send_messages(
        NewConversationMessage(
            content=setup_welcome,
            message_type=MessageType.chat,
            metadata={"generated_content": False},
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
    from .mission_storage import ConversationMissionManager
    from .mission_tools import MissionTools, get_mission_tools

    # First check conversation metadata
    conversation = await context.get_conversation()
    metadata = conversation.metadata or {}
    metadata_role = metadata.get("mission_role")

    # Then check the stored role from mission storage - this is the authoritative source
    stored_role = await ConversationMissionManager.get_conversation_role(context)
    stored_role_value = stored_role.value if stored_role else None

    # Log the roles we find for debugging
    logger.info(f"Role detection - Metadata role: {metadata_role}, Stored role: {stored_role_value}")

    # If we have a stored role but metadata is different or missing, update metadata
    if stored_role_value and metadata_role != stored_role_value:
        logger.warning(f"Role mismatch detected! Metadata: {metadata_role}, Storage: {stored_role_value}")
        metadata["mission_role"] = stored_role_value
        # Update state to ensure UI is refreshed
        await context.send_conversation_state_event(
            AssistantStateEvent(state_id="mission_role", event="updated", state=None)
        )
        # Force use of stored role
        role = stored_role_value
    else:
        # If no mismatch or no stored role, use metadata role (defaulting to HQ)
        role = metadata_role or "hq"  # Default to HQ if not set

    logger.info(f"Using role: {role} for tool selection")

    # For field role, analyze message for possible field request needs
    if role == "field" and message.message_type == MessageType.chat:
        # Create a mission tools instance for field role
        mission_tools_instance = MissionTools(context, role)

        # Check if the message indicates a potential field request
        detection_result = await mission_tools_instance.detect_field_request_needs(message.content)

        # If a field request is detected with reasonable confidence
        if detection_result.get("is_field_request", False) and detection_result.get("confidence", 0) > 0.5:
            # Get detailed information from detection
            suggested_title = detection_result.get("potential_title", "")
            suggested_priority = detection_result.get("suggested_priority", "medium")
            potential_description = detection_result.get("potential_description", "")
            reason = detection_result.get("reason", "")

            # Create a better-formatted suggestion using the detailed analysis
            suggestion = (
                f"**Field Request Detected**\n\n"
                f"It appears that you might need information from HQ. {reason}\n\n"
                f"Would you like me to create a field request?\n"
                f"**Title:** {suggested_title}\n"
                f"**Description:** {potential_description}\n"
                f"**Priority:** {suggested_priority}\n\n"
                f"I can create this request for you, or you can use `/request-info` to create it yourself with custom details."
            )

            await context.send_messages(
                NewConversationMessage(
                    content=suggestion,
                    message_type=MessageType.notice,
                )
            )

    # Create tool instance for the current role
    mission_tools = await get_mission_tools(context, role)

    # Define explicit lists of available tools for each role
    hq_available_tools = [
        "get_mission_info",
        "create_mission_briefing",
        "add_mission_goal",
        "add_kb_section",
        "resolve_field_request",
        "mark_mission_ready_for_field",
        "suggest_next_action",
    ]

    field_available_tools = [
        "get_mission_info",
        "create_field_request",
        "update_mission_status",
        "mark_criterion_completed",
        "report_mission_completion",
        "detect_field_request_needs",
        "suggest_next_action",
    ]

    # Get the available tools for the current role
    available_tools = hq_available_tools if role == "hq" else field_available_tools

    # Create a string listing available tools for the current role
    available_tools_str = ", ".join([f"`{tool}`" for tool in available_tools])

    # Create a string listing unauthorized tools to explicitly forbid
    forbidden_tools = field_available_tools if role == "hq" else hq_available_tools
    forbidden_tools_str = ", ".join([f"`{tool}`" for tool in forbidden_tools])

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
                logger.info(f"Using tool functions for completions (role: {role})")

                # Record the tool names available for this role for validation
                available_tool_names = set(mission_tools.tool_functions.function_map.keys())
                logger.info(f"Available tools for {role}: {available_tool_names}")

                # Construct a comprehensive role enforcement message
                if role == "hq":
                    role_enforcement = f"""
\n\n⚠️ CRITICAL TOOL ACCESS RESTRICTIONS ⚠️

As an HQ agent, you can ONLY use these tools: {available_tools_str}

You are FORBIDDEN from using these Field-only tools: {forbidden_tools_str}

If you need to perform a task normally done by a Field agent, you must instruct the user to switch to a Field conversation.

IMPORTANT PROCEDURE FOR RESOLVING FIELD REQUESTS:
1. FIRST run: get_mission_info(info_type="requests")
2. From the output, copy the exact Request ID (NOT the title)
3. THEN run: resolve_field_request(request_id="exact-id-from-step-1", resolution="your detailed response")
"""
                else:  # field role
                    role_enforcement = f"""
\n\n⚠️ CRITICAL TOOL ACCESS RESTRICTIONS ⚠️

As a FIELD agent, you can ONLY use these tools: {available_tools_str}

You are FORBIDDEN from using these HQ-only tools: {forbidden_tools_str}

If you need information from HQ, you MUST use the `create_field_request` tool to send a request to HQ.
DO NOT attempt to use HQ tools directly as they will fail and waste the user's time.
"""

                # Append the enforcement text to the role_specific_prompt
                role_specific_prompt += role_enforcement

                # The modified role_specific_prompt will be included in the system message
                # by respond_to_conversation call, which avoids any type issues

                # Make the API call
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
    response_message = await context.send_messages(
        NewConversationMessage(
            content=str(content) if content is not None else "[no response from openai]",
            message_type=message_type,
            metadata=metadata,
        )
    )
    
    # Manually capture assistant's message for HQ conversation storage
    # This ensures that both user and assistant messages are stored
    conversation = await context.get_conversation()
    metadata = conversation.metadata or {}
    role = metadata.get("mission_role")
    
    if role == "hq" and message_type == MessageType.chat and response_message and response_message.messages:
        try:
            # Get the mission ID
            from .mission_manager import MissionManager
            mission_id = await MissionManager.get_mission_id(context)
            
            if mission_id:
                for msg in response_message.messages:
                    # Store the assistant's message for Field access
                    from .mission_storage import MissionStorage
                    
                    MissionStorage.append_hq_message(
                        mission_id=mission_id,
                        message_id=str(msg.id),
                        content=msg.content,
                        sender_name=context.assistant.name,
                        is_assistant=True,
                        timestamp=msg.timestamp,
                    )
                    logger.info(f"Stored HQ assistant message for Field access: {msg.id}")
        except Exception as e:
            # Don't fail message handling if storage fails
            logger.exception(f"Error storing HQ assistant message for Field access: {e}")


# this method is used to get the token count of a string.
def get_token_count(string: str) -> int:
    """
    Get the token count of a string.
    """
    encoding = tiktoken.get_encoding("cl100k_base")
    return len(encoding.encode(string))


# endregion
