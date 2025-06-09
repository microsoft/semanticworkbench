import re
import time
from textwrap import dedent
from typing import Any, Dict, List

import openai_client
from assistant_extensions.attachments import AttachmentsExtension
from openai import BaseModel
from openai.types.chat import (
    ChatCompletionAssistantMessageParam,
    ChatCompletionMessageParam,
    ChatCompletionSystemMessageParam,
    ChatCompletionUserMessageParam,
)
from openai_client import num_tokens_from_messages
from openai_client.completion import message_content_from_completion
from openai_client.tools import complete_with_tool_calls
from pydantic import Field
from semantic_workbench_api_model.workbench_model import (
    ConversationMessage,
    ConversationParticipantList,
    MessageType,
    NewConversationMessage,
)
from semantic_workbench_assistant.assistant_app import (
    ConversationContext,
)

from .analysis import detect_information_request_needs
from .common import detect_assistant_role
from .config import assistant_config
from .data import RequestStatus
from .logging import logger
from .manager import ProjectManager
from .storage import ProjectStorage
from .storage_models import ConversationRole, CoordinatorConversationMessage
from .string_utils import Context, ContextStrategy, Instructions, Prompt, TokenBudget
from .tools import ProjectTools
from .utils import load_text_include

SILENCE_TOKEN = "{{SILENCE}}"


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
    new_message: ConversationMessage,
    attachments_extension: AttachmentsExtension,
    metadata: Dict[str, Any],
) -> None:
    """
    Respond to a conversation message.
    """
    if "debug" not in metadata:
        metadata["debug"] = {}

    # Config
    config = await assistant_config.get(context.assistant)
    model = config.request_config.openai_model

    # Requirements
    role = await detect_assistant_role(context)
    metadata["debug"]["role"] = role
    project_id = await ProjectManager.get_project_id(context)
    if not project_id:
        raise ValueError("Project ID not found in context")

    token_budget = TokenBudget(config.request_config.max_tokens)

    ##
    ## INSTRUCTIONS
    ##

    # Add role-specific instructions.
    if role == ConversationRole.COORDINATOR:
        assistant_role = config.prompt_config.coordinator_role
        role_specific_instructions = config.prompt_config.coordinator_instructions
    else:
        assistant_role = config.prompt_config.team_role
        role_specific_instructions = config.prompt_config.team_instructions
    instructions = Instructions(role_specific_instructions)

    # Add whiteboard instructions.
    instructions.add_subsection(
        Instructions(
            load_text_include("whiteboard_instructions.txt"),
            "Assistant Whiteboard",
        )
    )

    # If this is a multi-participant conversation, add a note about the participants.
    participants = await context.get_participants(include_inactive=True)
    if len(participants.participants) > 2:
        participant_text = (
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
        instructions.add_subsection(Instructions(participant_text, "Multi-participant conversation instructions"))

    prompt = Prompt(
        role=assistant_role,
        instructions=instructions,
        context_strategy=ContextStrategy.MULTI,
        output_format="Respond as JSON with your response in the `response` field and all citations in the `citations` field. In the `next_step_suggestion` field, suggest more areas to explore using content from the assistant whiteboard to ensure your conversation covers all of the relevant information.",
    )

    ###
    ### Context
    ###

    # Project info
    project_info = ProjectStorage.read_project_info(project_id)
    if project_info:
        data = project_info.model_dump()

        # Delete fields that are not relevant to the knowledge transfer assistant.
        # FIXME: Reintroduce these properly.
        if "state" in data:
            del data["state"]
        if "progress_percentage" in data:
            del data["progress_percentage"]
        if "completed_criteria" in data:
            del data["completed_criteria"]
        if "total_criteria" in data:
            del data["total_criteria"]
        if "lifecycle" in data:
            del data["lifecycle"]

        project_info_text = project_info.model_dump_json(indent=2)
        prompt.contexts.append(Context("Knowledge Info", project_info_text))

    # Brief
    briefing = ProjectStorage.read_project_brief(project_id)
    project_brief_text = ""
    if briefing:
        project_brief_text = f"**Title:** {briefing.title}\n**Description:** {briefing.description}"
        prompt.contexts.append(
            Context(
                "Knowledge Brief",
                project_brief_text,
            )
        )

    # Project goals
    project = ProjectStorage.read_project(project_id)
    if project and project.goals:
        goals_text = ""
        for i, goal in enumerate(project.goals):
            # Count completed criteria
            completed = sum(1 for c in goal.success_criteria if c.completed)
            total = len(goal.success_criteria)

            project_brief_text += f"{i + 1}. **{goal.name}** - {goal.description}\n"
            if goal.success_criteria:
                goals_text += f"   Progress: {completed}/{total} criteria complete\n"
                for criterion in goal.success_criteria:
                    check = "✅" if criterion.completed else "⬜"
                    goals_text += f"   {check} {criterion.description}\n"
        prompt.contexts.append(
            Context(
                "Project Goals",
                goals_text,
            )
        )

    # Whiteboard
    whiteboard = ProjectStorage.read_project_whiteboard(project_id)
    if whiteboard and whiteboard.content:
        prompt.contexts.append(Context("Assistant Whiteboard", whiteboard.content, "The assistant's whiteboard"))

    # Information requests
    all_requests = ProjectStorage.get_all_information_requests(project_id)
    if role == ConversationRole.COORDINATOR:
        active_requests = [r for r in all_requests if r.status != RequestStatus.RESOLVED]
        if active_requests:
            coordinator_requests = "> 📋 **Use the request ID (not the title) with resolve_information_request()**\n\n"
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
        else:
            coordinator_requests = "No active information requests."
        prompt.contexts.append(
            Context(
                "Information Requests",
                coordinator_requests,
            )
        )
    else:  # team role
        information_requests_info = ""
        my_requests = []

        # Filter for requests from this conversation that aren't resolved.
        my_requests = [
            r for r in all_requests if r.conversation_id == str(context.id) and r.status != RequestStatus.RESOLVED
        ]

        if my_requests:
            information_requests_info = ""
            for req in my_requests:
                information_requests_info += f"- **{req.title}** (ID: `{req.request_id}`, Priority: {req.priority})\n"
            information_requests_info += (
                '\nYou can delete any of these requests using `delete_information_request(request_id="the_id")`\n'
            )
        else:
            information_requests_info = "No active information requests."

        prompt.contexts.append(
            Context(
                "Information Requests",
                information_requests_info,
            )
        )

    # Calculate token count for all system messages so far.
    completion_messages = prompt.messages()
    token_budget.add(
        num_tokens_from_messages(
            model=model,
            messages=completion_messages,
        )
    )

    ###
    ### Coordinator conversation as an attachment.
    ###

    # Get the coordinator conversation and add it as an attachment.
    coordinator_conversation = ProjectStorage.read_coordinator_conversation(project_id)
    if coordinator_conversation:
        # Limit messages to the configured max token count.
        total_coordinator_conversation_tokens = 0
        selected_coordinator_conversation_messages: List[CoordinatorConversationMessage] = []
        for msg in reversed(coordinator_conversation.messages):
            tokens = openai_client.num_tokens_from_string(msg.model_dump_json(), model=model)
            if (
                total_coordinator_conversation_tokens + tokens
                > config.request_config.coordinator_conversation_token_limit
            ):
                break
            selected_coordinator_conversation_messages.append(msg)
            total_coordinator_conversation_tokens += tokens

        # Create a new coordinator conversation system message with the selected messages.
        class CoordinatorMessageList(BaseModel):
            messages: List[CoordinatorConversationMessage] = Field(default_factory=list)

        selected_coordinator_conversation_messages.reverse()
        coordinator_message_list = CoordinatorMessageList(messages=selected_coordinator_conversation_messages)
        coordinator_conversation_message = ChatCompletionSystemMessageParam(
            role="system",
            content=(
                f"<ATTACHMENT><FILENAME>CoordinatorConversation.json</FILENAME><CONTENT>{coordinator_message_list.model_dump_json()}</CONTENT>"
            ),
        )
        completion_messages.append(coordinator_conversation_message)

        token_budget.add(
            num_tokens_from_messages(
                model=model,
                messages=[coordinator_conversation_message],
            )
        )

    ###
    ### ATTACHMENTS
    ###

    # TODO: A better pattern here might be to keep the attachements as user
    # in the proper flow of the conversation rather than as .

    # Generate the attachment messages.
    attachment_messages: List[ChatCompletionMessageParam] = openai_client.convert_from_completion_messages(
        await attachments_extension.get_completion_messages_for_attachments(
            context,
            config=config.attachments_config,
        )
    )

    # TODO: This will exceed the token limit if there are too many attachments.
    # We do give them a warning below, though, and tell them to remove
    # attachments if this happens.

    token_budget.add(
        num_tokens_from_messages(
            model=model,
            messages=attachment_messages,
        )
    )
    completion_messages.extend(attachment_messages)

    ###
    ### USER MESSAGE
    ###

    if new_message.sender.participant_id == context.assistant.id:
        user_message: ChatCompletionMessageParam = ChatCompletionAssistantMessageParam(
            role="assistant",
            content=format_message(participants, new_message),
        )
    else:
        user_message: ChatCompletionMessageParam = ChatCompletionUserMessageParam(
            role="user",
            content=format_message(participants, new_message),
        )

    token_budget.add(
        num_tokens_from_messages(
            model=model,
            messages=[user_message],
        )
    )

    ###
    ### HISTORY MESSAGES
    ###

    history_messages: list[ChatCompletionMessageParam] = []
    before_message_id = new_message.id
    history_token_budget = TokenBudget(token_budget.remaining())

    # Fetch messages from the workbench in batches that will fit our token budget.
    under_budget = True
    while under_budget:
        # Get a batch of messages
        messages_response = await context.get_messages(
            before=before_message_id,
            limit=100,
            message_types=[MessageType.chat],
        )
        messages_list = messages_response.messages
        if not messages_list or len(messages_list) == 0:
            break
        before_message_id = messages_list[0].id

        for msg in reversed(messages_list):
            if msg.sender.participant_id == context.assistant.id:
                current_message = ChatCompletionAssistantMessageParam(
                    role="assistant",
                    content=format_message(participants, msg),
                )
            else:
                current_message = ChatCompletionUserMessageParam(
                    role="user",
                    content=format_message(participants, msg),
                )

            current_message_tokens = num_tokens_from_messages(
                model=model,
                messages=[current_message],
            )

            if history_token_budget.fits(current_message_tokens):
                history_messages = [current_message] + history_messages
                history_token_budget.add(current_message_tokens)
            else:
                under_budget = False
                break

        if not under_budget:
            break

    # Add all chat messages.
    completion_messages.extend(history_messages)
    completion_messages.append(user_message)

    # Add a system message to indicate attachments are a part of the new message.
    if new_message.filenames and len(new_message.filenames) > 0:
        attachment_message = ChatCompletionSystemMessageParam(
            role="system",
            content=f"Attachment(s): {', '.join(new_message.filenames)}",
        )
        completion_messages.append(attachment_message)
        token_budget.add(
            num_tokens_from_messages(
                model=model,
                messages=[attachment_message],
            )
        )

    ##
    ## Final token count check
    ##
    token_counts = {"total": token_budget.used, "max": token_budget.budget}
    metadata["debug"]["token_usage"] = token_counts  # For debug.
    metadata["token_counts"] = token_counts  # For footer.
    if token_budget.remaining() < 0:
        raise ValueError(
            f"You've exceeded the token limit of {token_budget.budget} in this conversation "
            f"({token_budget.used}). Try removing some attachments."
        )

    # For team role, analyze message for possible information request needs.
    # Send a notification if we think it might be one.
    if role is ConversationRole.TEAM:
        detection_result = await detect_information_request_needs(context, new_message.content)

        if detection_result.get("is_information_request", False) and detection_result.get("confidence", 0) > 0.8:
            suggested_title = detection_result.get("potential_title", "")
            suggested_priority = detection_result.get("suggested_priority", "medium")
            potential_description = detection_result.get("potential_description", "")
            reason = detection_result.get("reason", "")

            suggestion = (
                f"**Potential _Information Request_ Detected**\n\n"
                f"It appears that you might need information from the knowledge coordinator. {reason}\n\n"
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

    class Output(BaseModel):
        """
        Attributes:
            citations: A list of citations from which the response is generated. There should always be at least one citation, but it can be empty if the assistant has no relevant information to cite.
            excerpt: A verbatim excerpt from one of the cited works that illustrates why this response was given. It should have enough context to get a good idea of what's in that part of the cited work. If there is no relevant excerpt, this will be None.
            next_step_suggestion: Suggest more areas to explore using content from the assistant whiteboard to ensure your conversation covers all of the relevant information.
        """

        citations: list[str] = Field(
            description="A list of citations from which the response is generated. There should always be at least one citation, but it can be empty if the assistant has no relevant information to cite.",
        )
        excerpt: str | None = Field(
            description="A verbatim excerpt from one of the cited works that illustrates why this response was given. It should have enough context to get a good idea of what's in that part of the cited work. If there is no relevant excerpt, this will be None.",
        )
        response: str = Field(
            description="The response from the assistant.",
        )
        next_step_suggestion: str = Field(
            description="Suggest more areas to explore using content from the assistant whiteboard to ensure your conversation covers all of the relevant information. For example: 'Would you like to explore ... next?'.",
        )

        model_config = {
            "extra": "forbid"  # This sets additionalProperties=false in the schema
        }

    async with openai_client.create_client(config.service_config) as client:
        try:
            completion_args = {
                "messages": completion_messages,
                "model": model,
                "max_tokens": config.request_config.response_tokens,
                "response_format": Output,
            }

            project_tools = ProjectTools(context, role)
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
            if completion_response:
                response_tokens = completion_response.usage.completion_tokens if completion_response.usage else 0
                request_tokens = token_budget.used
                footer_items.append(
                    get_token_usage_message(
                        max_tokens=config.request_config.max_tokens,
                        total_tokens=request_tokens + response_tokens,
                        request_tokens=request_tokens,
                        completion_tokens=response_tokens,
                    )
                )

                await context.update_conversation(
                    metadata={
                        "token_counts": {
                            "total": request_tokens + response_tokens,
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
                metadata["debug"]["silence_token"] = True
                metadata["debug"]["silence_token_response"] = (content,)
                await context.send_messages(
                    NewConversationMessage(
                        message_type=MessageType.notice,
                        content="[assistant chose to remain silent]",
                        metadata=metadata,
                    )
                )
            return

    # Prepare response and citations.
    response_parts: list[str] = []
    try:
        output_model = Output.model_validate_json(content)
        if output_model.response:
            response_parts.append(output_model.response)

        if role == ConversationRole.TEAM and output_model.excerpt:
            output_model.excerpt = output_model.excerpt.strip().strip('"')
            response_parts.append(f'> _"{output_model.excerpt}"_ (excerpt)')

        if role == ConversationRole.TEAM and output_model.next_step_suggestion:
            response_parts.append(output_model.next_step_suggestion)

        if role == ConversationRole.TEAM and output_model.citations:
            citations = ", ".join(output_model.citations)
            response_parts.append(f"Sources: _{citations}_")

    except Exception as e:
        logger.exception(f"exception occurred parsing json response: {e}")
        metadata["debug"]["error"] = str(e)
        response_parts.append(content)

    await context.send_messages(
        NewConversationMessage(
            content="\n\n".join(response_parts),
            message_type=MessageType.chat,
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
