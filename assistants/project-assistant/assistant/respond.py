import re
import time
from textwrap import dedent
from typing import Any, Dict, List

import openai_client
from assistant_extensions.attachments import AttachmentsExtension
from openai.types.chat import (
    ChatCompletionAssistantMessageParam,
    ChatCompletionMessageParam,
    ChatCompletionSystemMessageParam,
    ChatCompletionUserMessageParam,
)
from openai_client.completion import message_content_from_completion
from openai_client.tools import complete_with_tool_calls
from semantic_workbench_api_model.workbench_model import (
    ConversationMessage,
    ConversationParticipantList,
    MessageType,
    NewConversationMessage,
)
from semantic_workbench_assistant.assistant_app import (
    ConversationContext,
)

from assistant.tools import ProjectTools

from .config import assistant_config
from .logging import logger
from .project_analysis import detect_information_request_needs
from .project_common import ConfigurationTemplate, detect_assistant_role, get_template
from .project_data import RequestStatus
from .project_manager import ProjectManager
from .project_storage import ProjectStorage
from .project_storage_models import ConversationRole

SILENCE_TOKEN = "{{SILENCE}}"
CONTEXT_TRANSFER_ASSISTANT = ConfigurationTemplate.CONTEXT_TRANSFER_ASSISTANT
PROJECT_ASSISTANT = ConfigurationTemplate.PROJECT_ASSISTANT


def is_project_assistant(context: ConversationContext) -> bool:
    """
    Check if the assistant is a project assistant.
    """
    template = get_template(context)
    return template == PROJECT_ASSISTANT


# Format message helper function
def format_message(participants: ConversationParticipantList, message: ConversationMessage) -> str:
    """Consistent formatter that includes the participant name for multi-participant and name references"""
    conversation_participant = next(
        (participant for participant in participants.participants if participant.id == message.sender.participant_id),
        None,
    )
    participant_name = conversation_participant.name if conversation_participant else "unknown"
    message_datetime = message.timestamp.strftime("%Y-%m-%d %H:%M:%S")
    return f"[{participant_name} - {message_datetime}]: {message.content}"


async def respond_to_conversation(
    context: ConversationContext,
    message: ConversationMessage,
    attachments_extension: AttachmentsExtension,
    metadata: Dict[str, Any],
) -> None:
    """
    Respond to a conversation message.
    """
    if "debug" not in metadata:
        metadata["debug"] = {}

    config = await assistant_config.get(context.assistant)

    role = await detect_assistant_role(context)
    metadata["debug"]["role"] = role
    template = get_template(context)
    metadata["debug"]["template"] = template

    max_tokens = config.request_config.max_tokens
    available_tokens = max_tokens

    ###
    ### SYSTEM MESSAGE
    ###

    # Instruction and assistant name
    system_message_content = (
        f'\n\n{config.prompt_config.instruction_prompt}\n\nYour name is "{context.assistant.name}".'
    )

    # Add role-specific instructions
    role_specific_prompt = ""
    if role == ConversationRole.COORDINATOR:
        role_specific_prompt = config.prompt_config.coordinator_prompt
    else:
        role_specific_prompt = config.prompt_config.team_prompt

    if role_specific_prompt:
        system_message_content += f"\n\n{role_specific_prompt}"

    # If this is a multi-participant conversation, add a note about the participants
    participants = await context.get_participants(include_inactive=True)
    if len(participants.participants) > 2:
        system_message_content += (
            "\n\n"
            f"There are {len(participants.participants)} participants in the conversation,"
            " including you as the assistant and the following users:"
            + ",".join([
                f' "{participant.name}"'
                for participant in participants.participants
                if participant.id != context.assistant.id
            ])
            + "\n\nYou do not need to respond to every message. Do not respond if the last thing said was a closing"
            " statement such as 'bye' or 'goodbye', or just a general acknowledgement like 'ok' or 'thanks'. Do not"
            f' respond as another user in the conversation, only as "{context.assistant.name}".'
            " Sometimes the other users need to talk amongst themselves and that is ok. If the conversation seems to"
            f' be directed at you or the general audience, go ahead and respond.\n\nSay "{SILENCE_TOKEN}" to skip'
            " your turn."
        )

    ###
    ### SYSTEM MESSAGE: Project information
    ###

    project_id = await ProjectManager.get_project_id(context)
    if not project_id:
        raise ValueError("Project ID not found in context")

    project_data = {}
    all_requests = []

    try:
        # Get comprehensive project data for prompt
        briefing = ProjectStorage.read_project_brief(project_id)
        project_info = ProjectStorage.read_project_info(project_id)
        whiteboard = ProjectStorage.read_project_whiteboard(project_id)
        all_requests = ProjectStorage.get_all_information_requests(project_id)

        # Include project info
        project_info_text = ""
        if project_info:
            project_info_text = f"""
### PROJECT INFO
**Current State:** {project_info.state.value}

**Full project info**
```json
{project_info.model_dump_json(indent=2)}
```
"""
            if project_info.status_message:
                project_info_text += f"**Status Message:** {project_info.status_message}\n"
            project_data["status"] = project_info_text

        # Include project brief
        project_brief_text = ""
        if briefing:
            # Basic project brief without goals
            project_brief_text = f"""
### PROJECT BRIEF
**Name:** {briefing.project_name}
**Description:** {briefing.project_description}
"""
            # Only include project goals and progress tracking if the assistant is a project assistant
            # First get the project to access its goals
            project_id = await ProjectManager.get_project_id(context)
            project = ProjectStorage.read_project(project_id) if project_id else None

            if is_project_assistant(context) and project and project.goals:
                project_brief_text += """
#### PROJECT GOALS:
"""
                for i, goal in enumerate(project.goals):
                    # Count completed criteria
                    completed = sum(1 for c in goal.success_criteria if c.completed)
                    total = len(goal.success_criteria)

                    project_brief_text += f"{i + 1}. **{goal.name}** - {goal.description}\n"
                    if goal.success_criteria:
                        project_brief_text += f"   Progress: {completed}/{total} criteria complete\n"
                        for j, criterion in enumerate(goal.success_criteria):
                            check = "✅" if criterion.completed else "⬜"
                            project_brief_text += f"   {check} {criterion.description}\n"
                    project_brief_text += "\n"
                project_data["briefing"] = project_brief_text

        # Include whiteboard content
        if whiteboard and whiteboard.content:
            whiteboard_text = f"""
### ASSISTANT WHITEBOARD - KEY PROJECT KNOWLEDGE
The whiteboard contains critical project information that has been automatically extracted from previous conversations.
It serves as a persistent memory of important facts, decisions, and context that you should reference when responding.

Key characteristics of this whiteboard:
- It contains the most essential information about the project that should be readily available
- It has been automatically curated to focus on high-value content relevant to the project
- It is maintained and updated as the conversation progresses
- It should be treated as a trusted source of contextual information for this project

When using the whiteboard:
- Prioritize this information when addressing questions or providing updates
- Reference it to ensure consistency in your responses across the conversation
- Use it to track important details that might otherwise be lost in the conversation history

WHITEBOARD CONTENT:
```markdown
{whiteboard.content}
```

"""
            project_data["whiteboard"] = whiteboard_text

    except Exception as e:
        logger.warning(f"Failed to fetch project data for prompt: {e}")

    # Construct role-specific messages with comprehensive project data
    if role == ConversationRole.COORDINATOR:
        # Include information requests

        active_requests = [r for r in all_requests if r.status != RequestStatus.RESOLVED]
        if active_requests:
            coordinator_requests = "\n\n### ACTIVE INFORMATION REQUESTS\n"
            coordinator_requests += "> 📋 **Use the request ID (not the title) with resolve_information_request()**\n\n"

            for req in active_requests[:10]:  # Limit to 10 for brevity
                priority_marker = {
                    "low": "🔹",
                    "medium": "🔶",
                    "high": "🔴",
                    "critical": "⚠️",
                }.get(req.priority.value, "🔹")

                coordinator_requests += f"{priority_marker} **{req.title}** ({req.status.value})\n"
                coordinator_requests += f"   **Request ID:** `{req.request_id}`\n"
                coordinator_requests += f"   **Description:** {req.description}\n\n"

            if len(active_requests) > 10:
                coordinator_requests += f'*...and {len(active_requests) - 10} more requests. Use get_project_info(info_type="requests") to see all.*\n'
            project_data["information_requests"] = coordinator_requests
        else:
            project_data["information_requests"] = (
                "\n\n### ACTIVE INFORMATION REQUESTS\nNo active information requests."
            )

    else:  # team role
        # Fetch current information requests for this conversation
        information_requests_info = ""
        my_requests = []

        if all_requests:
            # Filter for requests from this conversation that aren't resolved
            my_requests = [
                r for r in all_requests if r.conversation_id == str(context.id) and r.status != RequestStatus.RESOLVED
            ]

            if my_requests:
                information_requests_info = "\n\n### YOUR CURRENT INFORMATION REQUESTS:\n"
                for req in my_requests:
                    information_requests_info += (
                        f"- **{req.title}** (ID: `{req.request_id}`, Priority: {req.priority})\n"
                    )
                information_requests_info += (
                    '\nYou can delete any of these requests using `delete_information_request(request_id="the_id")`\n'
                )
                project_data["information_requests"] = information_requests_info

    # Add project data to system message
    project_info = "\n\n## CURRENT PROJECT INFORMATION\n\n" + "\n".join(project_data.values())
    system_message_content += f"\n\n{project_info}"
    system_message: ChatCompletionMessageParam = {
        "role": "system",
        "content": system_message_content,
    }

    # Calculate token count for the system message
    system_message_tokens = openai_client.num_tokens_from_messages(
        model=config.request_config.openai_model,
        messages=[system_message],
    )
    available_tokens -= system_message_tokens

    # Initialize message list with system message
    completion_messages: list[ChatCompletionMessageParam] = [
        system_message,
    ]

    ###
    ### ATTACHMENTS
    ###

    # Generate the attachment messages
    attachment_messages: List[ChatCompletionMessageParam] = openai_client.convert_from_completion_messages(
        await attachments_extension.get_completion_messages_for_attachments(
            context,
            config=config.attachments_config,
        )
    )

    # Update token count to include attachment messages
    attachment_tokens = openai_client.num_tokens_from_messages(
        model=config.request_config.openai_model,
        messages=attachment_messages,
    )
    available_tokens -= attachment_tokens

    # Add attachment messages to completion messages
    completion_messages.extend(attachment_messages)

    ###
    ### USER MESSAGE
    ###

    # Format the current message
    # Create the message parameter based on sender with proper typing
    if message.sender.participant_id == context.assistant.id:
        user_message: ChatCompletionMessageParam = ChatCompletionAssistantMessageParam(
            role="assistant",
            content=format_message(participants, message),
        )
    else:
        user_message: ChatCompletionMessageParam = ChatCompletionUserMessageParam(
            role="user",
            content=format_message(participants, message),
        )

    # Calculate tokens for this message
    user_message_tokens = openai_client.num_tokens_from_messages(
        model=config.request_config.openai_model,
        messages=[user_message],
    )
    available_tokens -= user_message_tokens

    ###
    ### HISTORY MESSAGES
    ###

    # Get the conversation history
    # For pagination, we'll retrieve messages in batches as needed
    history_messages: list[ChatCompletionMessageParam] = []
    before_message_id = message.id

    # Track token usage and overflow
    history_messages_tokens = 0
    token_overage = 0

    # We'll fetch messages in batches until we hit the token limit or run out of messages
    while True:
        # Get a batch of messages
        messages_response = await context.get_messages(
            before=before_message_id,
            limit=100,  # Get messages in batches of 100
            message_types=[MessageType.chat],  # Include only chat messages
        )

        messages_list = messages_response.messages

        # If no messages found, break the loop
        if not messages_list or len(messages_list) == 0:
            break

        # Set before_message_id for the next batch
        before_message_id = messages_list[0].id

        # Process messages in reverse order (oldest first for history)
        for msg in reversed(messages_list):
            # Format this message for inclusion
            formatted_message = format_message(participants, msg)

            # Create the message parameter based on sender with proper typing
            is_assistant = msg.sender.participant_id == context.assistant.id
            if is_assistant:
                current_message = ChatCompletionAssistantMessageParam(
                    role="assistant",
                    content=formatted_message,
                )
            else:
                current_message = ChatCompletionUserMessageParam(
                    role="user",
                    content=formatted_message,
                )

            # Calculate tokens for this message
            user_message_tokens = openai_client.num_tokens_from_messages(
                model=config.request_config.openai_model,
                messages=[current_message],
            )

            # Check if we can add this message without exceeding the token limit
            if token_overage == 0 and history_messages_tokens + user_message_tokens < available_tokens:
                # Add message to the front of history_messages (to maintain chronological order)
                history_messages = [current_message] + history_messages
                history_messages_tokens += user_message_tokens
            else:
                # We've exceeded the token limit, track the overage
                token_overage += user_message_tokens

        # If we've already exceeded the token limit, no need to fetch more messages
        if token_overage > 0:
            break

    # Add all chat messages.
    completion_messages.extend(history_messages)
    completion_messages.append(user_message)

    if message.filenames and len(message.filenames) > 0:
        # add a system message to indicate attachments are a part of the user message
        attachment_message = ChatCompletionSystemMessageParam(
            role="system",
            content=f"Attachment(s): {', '.join(message.filenames)}",
        )
        completion_messages.append(attachment_message)
        attachment_message_tokens = openai_client.num_tokens_from_messages(
            model=config.request_config.openai_model,
            messages=[attachment_message],
        )
        available_tokens -= attachment_message_tokens

    ##
    ## TOKEN COUNT HANDLING
    ##
    total_tokens = max_tokens - available_tokens
    metadata["debug"]["token_usage"] = {"total": total_tokens, "max": max_tokens}
    metadata["token_counts"] = {
        "total": total_tokens,
        "max": config.request_config.max_tokens,
    }

    if available_tokens < 0:
        raise ValueError(
            f"You've exceeded the token limit of {config.request_config.max_tokens} in this conversation "
            f"({total_tokens}). Try removing some attachments."
        )

    # These are the tools that are available to the assistant.
    project_tools = ProjectTools(context, role)

    # For team role, analyze message for possible information request needs.
    # Send a notification if we think it might be one.
    if role is ConversationRole.TEAM:
        detection_result = await detect_information_request_needs(context, message.content)

        if detection_result.get("is_information_request", False) and detection_result.get("confidence", 0) > 0.8:
            suggested_title = detection_result.get("potential_title", "")
            suggested_priority = detection_result.get("suggested_priority", "medium")
            potential_description = detection_result.get("potential_description", "")
            reason = detection_result.get("reason", "")

            suggestion = (
                f"**Information Request Detected**\n\n"
                f"It appears that you might need information from the Coordinator. {reason}\n\n"
                f"Would you like me to create an information request?\n"
                f"**Title:** {suggested_title}\n"
                f"**Description:** {potential_description}\n"
                f"**Priority:** {suggested_priority}\n\n"
            )

            await context.send_messages(
                NewConversationMessage(
                    content=suggestion,
                    message_type=MessageType.notice,
                    metadata={"debug": detection_result},
                )
            )
        metadata["debug"]["detection_result"] = detection_result

    ##
    ## MAKE THE LLM CALL
    ##

    async with openai_client.create_client(config.service_config) as client:
        try:
            # Create a completion dictionary for tool call handling
            completion_args = {
                "messages": completion_messages,
                "model": config.request_config.openai_model,
                "max_tokens": config.request_config.response_tokens,
            }

            # Call the completion API with tool functions
            logger.info(f"Using tool functions for completions (role: {role})")

            # Record the tool names available for this role for validation
            available_tool_names = set(project_tools.tool_functions.function_map.keys())
            logger.info(f"Available tools for {role}: {available_tool_names}")

            # Make the API call
            response_start_time = time.time()
            completion_response, additional_messages = await complete_with_tool_calls(
                async_client=client,
                completion_args=completion_args,
                tool_functions=project_tools.tool_functions,
                metadata=metadata["debug"],
            )
            response_end_time = time.time()
            footer_items = []

            # Add the token usage message to the footer items
            if completion_response and total_tokens > 0:
                completion_tokens = completion_response.usage.completion_tokens if completion_response.usage else 0
                request_tokens = total_tokens - completion_tokens
                footer_items.append(
                    get_token_usage_message(
                        max_tokens=config.request_config.max_tokens,
                        total_tokens=total_tokens,
                        request_tokens=request_tokens,
                        completion_tokens=completion_tokens,
                    )
                )

                await context.update_conversation(
                    metadata={
                        "token_counts": {
                            "total": total_tokens,
                            "max": config.request_config.max_tokens,
                        }
                    }
                )

            footer_items.append(get_response_duration_message(response_end_time - response_start_time))
            metadata["footer_items"] = footer_items

            content = message_content_from_completion(completion_response)
            if not content:
                content = "I've processed your request, but couldn't generate a proper response."

        except Exception as e:
            logger.exception(f"exception occurred calling openai chat completion: {e}")
            content = "An error occurred while calling the OpenAI API. Is it configured correctly?"
            metadata["debug"]["error"] = str(e)

    message_type = MessageType.chat
    if content:
        # strip out the username from the response
        if isinstance(content, str) and content.startswith("["):
            content = re.sub(r"\[.*\]:\s", "", content)

        # check for the silence token, in case the model chooses not to respond
        # model sometimes puts extra spaces in the response, so remove them
        # when checking for the silence token
        if isinstance(content, str) and content.replace(" ", "") == SILENCE_TOKEN:
            # normal behavior is to not respond if the model chooses to remain silent
            # but we can override this behavior for debugging purposes via the assistant config
            if config.enable_debug_output:
                # update the metadata to indicate the assistant chose to remain silent
                metadata["debug"]["silence_token"] = True
                metadata["debug"]["silence_token_response"] = (content,)
                # send a notice to the user that the assistant chose to remain silent
                await context.send_messages(
                    NewConversationMessage(
                        message_type=MessageType.notice,
                        content="[assistant chose to remain silent]",
                        metadata=metadata,
                    )
                )
            return

    await context.send_messages(
        NewConversationMessage(
            content=str(content) if content is not None else "[no response from openai]",
            message_type=message_type,
            metadata=metadata,
        )
    )


def get_formatted_token_count(tokens: int) -> str:
    # if less than 1k, return the number of tokens
    # if greater than or equal to 1k, return the number of tokens in k
    # use 1 decimal place for k
    # drop the decimal place if the number of tokens in k is a whole number
    if tokens < 1000:
        return str(tokens)
    else:
        tokens_in_k = tokens / 1000
        if tokens_in_k.is_integer():
            return f"{int(tokens_in_k)}k"
        else:
            return f"{tokens_in_k:.1f}k"


def get_token_usage_message(
    max_tokens: int,
    total_tokens: int,
    request_tokens: int,
    completion_tokens: int,
) -> str:
    """
    Generate a display friendly message for the token usage, to be added to the footer items.
    """

    return dedent(f"""
        Tokens used: {get_formatted_token_count(total_tokens)}
        ({get_formatted_token_count(request_tokens)} in / {get_formatted_token_count(completion_tokens)} out)
        of {get_formatted_token_count(max_tokens)} ({int(total_tokens / max_tokens * 100)}%)
    """).strip()


def get_response_duration_message(response_duration: float) -> str:
    """
    Generate a display friendly message for the response duration, to be added to the footer items.
    """

    return f"Response time: {response_duration:.2f} seconds"
