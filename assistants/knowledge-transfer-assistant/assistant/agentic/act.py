import time
from textwrap import dedent
from typing import Any, ClassVar

import openai_client
from assistant_extensions.attachments import AttachmentsExtension
from openai import BaseModel
from openai.types.chat import (
    ChatCompletionAssistantMessageParam,
)
from openai_client import num_tokens_from_messages
from openai_client.completion import assistant_message_from_completion
from openai_client.errors import CompletionError
from openai_client.tools import complete_with_tool_calls
from pydantic import ConfigDict, Field
from semantic_workbench_api_model.workbench_model import (
    MessageType,
    NewConversationMessage,
)
from semantic_workbench_assistant.assistant_app import (
    ConversationContext,
)

from assistant.config import assistant_config
from assistant.domain.share_manager import ShareManager
from assistant.logging import logger
from assistant.prompt_utils import (
    ContextSection,
    ContextStrategy,
    Instructions,
    Prompt,
    TokenBudget,
    add_context_to_prompt,
)
from assistant.tools import ShareTools
from assistant.utils import load_text_include


class ActorOutput(BaseModel):
    """
    Attributes:
        response: The response from the assistant.
    """

    accomplishments: str = Field(
        description="A summary of all the actions performed and their results.",
    )
    user_information_requests: list[str] = Field(
        description="A list of all the information requests that were made during the conversation.",
    )
    model_config: ClassVar[ConfigDict] = ConfigDict(extra="forbid")


async def act(
    context: ConversationContext,
    attachments_extension: AttachmentsExtension,
    metadata: dict[str, Any],
) -> ChatCompletionAssistantMessageParam | None:
    """
    Work, work, work, work, work...
    """

    if "debug" not in metadata:
        metadata["debug"] = {}

    config = await assistant_config.get(context.assistant)
    model = config.request_config.openai_model
    role = await ShareManager.get_conversation_role(context)
    metadata["debug"]["role"] = role
    token_budget = TokenBudget(config.request_config.max_tokens)

    instructions = load_text_include("detect_knowledge_package_gaps.md")
    instructions = Instructions(instructions)
    prompt = Prompt(
        instructions=instructions,
        context_strategy=ContextStrategy.MULTI,
    )
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
        ContextSection.COORDINATOR_CONVERSATION,
    ]
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

    # Calculate token count for all prompt so far.
    completion_messages = prompt.messages()
    token_budget.add(
        num_tokens_from_messages(
            model=model,
            messages=completion_messages,
        )
    )

    content = ""
    async with openai_client.create_client(config.service_config) as client:
        try:
            completion_args = {
                "messages": completion_messages,
                "model": model,
                "max_tokens": config.request_config.response_tokens,
                "temperature": 0.7,
                "response_format": ActorOutput,
            }

            share_tools = ShareTools(context, role)
            response_start_time = time.time()
            completion_response, _ = await complete_with_tool_calls(
                async_client=client,
                completion_args=completion_args,
                tool_functions=share_tools.tool_functions,
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
