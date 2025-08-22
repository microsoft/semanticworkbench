import time
from textwrap import dedent
from typing import Any, ClassVar

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
from openai_client.completion import assistant_message_from_completion
from openai_client.errors import CompletionError
from openai_client.tools import complete_with_tool_calls
from pydantic import ConfigDict, Field
from semantic_workbench_api_model.workbench_model import (
    ConversationMessage,
    ConversationParticipantList,
    MessageType,
    NewConversationMessage,
)
from semantic_workbench_assistant.assistant_app import (
    ConversationContext,
)

from assistant.config import assistant_config
from assistant.data import ConversationRole
from assistant.domain.conversation_preferences_manager import (
    ConversationPreferencesManager,
)
from assistant.domain.share_manager import ShareManager
from assistant.logging import logger
from assistant.prompt_utils import (
    ContextSection,
    ContextStrategy,
    DataContext,
    Instructions,
    Prompt,
    TokenBudget,
    add_context_to_prompt,
)
from assistant.tools import ShareTools
from assistant.utils import load_text_include

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


class CoordinatorOutput(BaseModel):
    """
    Attributes:
        response: The response from the assistant.
    """

    response: str = Field(
        description="The response from the assistant. The response should not duplicate information from the excerpt but may refer to it.",  # noqa: E501
    )

    model_config: ClassVar[ConfigDict] = ConfigDict(extra="forbid")


class TeamOutput(BaseModel):
    """
    Attributes:
        citations: A list of citations from which the response is generated. There should always be at least one citation, but it can be empty if the assistant has no relevant information to cite.
        excerpt: A verbatim excerpt from one of the cited works that illustrates why this response was given. It should have enough context to get a good idea of what's in that part of the cited work. DO NOT excerpt from CONVERSATION or DIGEST, only from attachments. If there is no relevant excerpt, this will be None. If there is special formatting in the excerpt, remove it as the excerpt will be displayed in quotes in a chat message and should not contain any formatting that would not be supported in a chat message (e.g. markdown).
        next_step_suggestion: Suggest more areas to explore using content from the knowledge digest to ensure your conversation covers all of the relevant information.
    """  # noqa: E501

    citations: list[str] = Field(
        description="A list of citations from which the response is generated. There should always be at least one citation, but it can be empty if the assistant has no relevant information to cite.",  # noqa: E501
    )
    excerpt: str | None = Field(
        description="A verbatim excerpt from one of the cited works that illustrates why this response was given. It should have enough context to get a good idea of what's in that part of the cited work. DO NOT excerpt from CONVERSATION or KNOWLEDGE_DIGEST, only from attachments. If there is no relevant excerpt, this will be None. If there is special formatting in the excerpt, remove it as the excerpt will be displayed in quotes in a chat message and should not contain any formatting that would not be supported in a chat message (e.g. markdown).",  # noqa: E501
    )
    response: str = Field(
        description="The response from the assistant. The response should not duplicate information from the excerpt but may refer to it.",  # noqa: E501
    )
    next_step_suggestion: str = Field(
        description="Suggest more areas to explore using content from the knowledge digest to ensure your conversation covers all of the relevant information. For example: 'Would you like to explore ... next?'.",  # noqa: E501
    )

    model_config: ClassVar[ConfigDict] = ConfigDict(extra="forbid")


async def respond_to_conversation(
    context: ConversationContext,
    new_message: ConversationMessage,
    attachments_extension: AttachmentsExtension,
    metadata: dict[str, Any],
    user_information_requests: list[str] | None = None,
) -> ChatCompletionAssistantMessageParam | None:
    """
    Respond to a conversation message.
    """
    if "debug" not in metadata:
        metadata["debug"] = {}

    config = await assistant_config.get(context.assistant)
    model = config.request_config.openai_model
    role = await ShareManager.get_conversation_role(context)
    metadata["debug"]["role"] = role
    token_budget = TokenBudget(config.request_config.max_tokens)

    ##
    ## INSTRUCTIONS
    ##

    # Add role-specific instructions.
    if role == ConversationRole.COORDINATOR:
        role_specific_instructions = config.prompt_config.coordinator_instructions
    else:
        role_specific_instructions = config.prompt_config.team_instructions
    instructions = Instructions(role_specific_instructions)

    # Add knowledge digest instructions.
    instructions.add_subsection(
        Instructions(
            load_text_include("knowledge_digest_instructions.txt"),
            "Assistant's Knowledge Digest",
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

    # Add conversation preferences instructions.
    communication_style = await ConversationPreferencesManager.get_preferred_communication_style(context)
    instructions.add_subsection(Instructions(communication_style, "Preferred Communication Style"))

    prompt = Prompt(
        instructions=instructions,
        context_strategy=ContextStrategy.MULTI,
    )
    if role == ConversationRole.TEAM:
        prompt.output_format = "Respond as JSON with your response in the `response` field and all citations in the `citations` field. In the `next_step_suggestion` field, suggest more areas to explore using content from the assistant whiteboard to ensure your conversation covers all of the relevant information."  # noqa: E501

    ##
    ## CONTEXT
    ##

    sections = [
        ContextSection.KNOWLEDGE_INFO,
        ContextSection.KNOWLEDGE_BRIEF,
        ContextSection.TARGET_AUDIENCE,
        # ContextSection.LEARNING_OBJECTIVES,
        ContextSection.KNOWLEDGE_DIGEST,
        ContextSection.INFORMATION_REQUESTS,
        # ContextSection.SUGGESTED_NEXT_ACTIONS,
        ContextSection.ATTACHMENTS,
        ContextSection.TASKS,
    ]
    if role == ConversationRole.TEAM:
        sections.append(ContextSection.COORDINATOR_CONVERSATION)

    await add_context_to_prompt(
        prompt,
        context=context,
        role=role,
        model=model,
        token_limit=config.request_config.max_tokens,
        attachments_extension=attachments_extension,
        attachments_config=config.attachments_config,
        attachments_in_system_message=False,
        include=sections,
    )

    user_information_requests_data = "- ".join(user_information_requests) if user_information_requests else "None"
    prompt.contexts.append(
        DataContext(
            "Information Needed from the User",
            user_information_requests_data,
        )
    )

    # Calculate token count for all prompt so far.
    completion_messages = prompt.messages()
    token_budget.add(
        num_tokens_from_messages(
            model=model,
            messages=completion_messages,
        )
    )

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
                # For assistant messages, include help suggestions as part of the message content
                message_content = format_message(participants, msg)
                if msg.metadata and "help" in msg.metadata:
                    message_content += f"\n\n[Next step?: {msg.metadata['help']}]"

                current_message = ChatCompletionAssistantMessageParam(
                    role="assistant",
                    content=message_content,
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
                history_messages = [current_message, *history_messages]
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

    ##
    ## MAKE THE LLM CALL
    ##

    content = ""
    async with openai_client.create_client(config.service_config) as client:
        try:
            completion_args = {
                "messages": completion_messages,
                "model": model,
                "max_tokens": config.request_config.response_tokens,
                "response_format": CoordinatorOutput if role == ConversationRole.COORDINATOR else TeamOutput,
            }

            share_tools = ShareTools(context)
            tool_functions = (
                share_tools.conversationalist_tools()
                if role == ConversationRole.COORDINATOR
                else share_tools.team_tools()
            )
            response_start_time = time.time()
            completion_response, _ = await complete_with_tool_calls(
                async_client=client,
                completion_args=completion_args,
                tool_functions=tool_functions,
                metadata=metadata["debug"],
                max_tool_call_rounds=32,
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
            return assistant_message_from_completion(completion_response) if completion_response else None

        except CompletionError as e:
            logger.exception(f"Exception occurred calling OpenAI chat completion: {e}")
            metadata["debug"]["error"] = str(e)
            if isinstance(e.body, dict) and "message" in e.body:
                content = e.body.get("message", e.message)
            elif e.message:
                content = e.message
            else:
                content = "An error occurred while processing your request."
            await context.send_messages(
                NewConversationMessage(
                    content=content,
                    message_type=MessageType.notice,
                    metadata=metadata,
                )
            )
            return


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
