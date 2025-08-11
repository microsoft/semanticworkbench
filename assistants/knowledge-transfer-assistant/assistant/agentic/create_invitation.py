from typing import Any

import openai_client
from semantic_workbench_assistant.assistant_app import ConversationContext

from assistant.config import assistant_config
from assistant.domain.share_manager import ShareManager
from assistant.logging import convert_to_serializable, logger
from assistant.notifications import Notifications
from assistant.prompt_utils import (
    ContextSection,
    ContextStrategy,
    Instructions,
    Prompt,
    add_context_to_prompt,
)
from assistant.utils import load_text_include


async def create_invitation(context: ConversationContext) -> str:
    debug: dict[str, Any] = {
        "context": convert_to_serializable(context.to_dict()),
    }

    config = await assistant_config.get(context.assistant)

    # Set up prompt instructions.
    instruction_text = load_text_include("create_invitation.md")
    instructions = Instructions(instruction_text)
    prompt = Prompt(
        instructions=instructions,
        context_strategy=ContextStrategy.MULTI,
    )

    # Add prompt context.
    role = await ShareManager.get_conversation_role(context)
    await add_context_to_prompt(
        prompt,
        context=context,
        role=role,
        model=config.request_config.openai_model,
        token_limit=config.request_config.max_tokens,
        attachments_config=config.attachments_config,
        attachments_in_system_message=True,
        include=[
            ContextSection.KNOWLEDGE_INFO,
            ContextSection.KNOWLEDGE_BRIEF,
            # ContextSection.TASKS,
            ContextSection.TARGET_AUDIENCE,
            # ContextSection.LEARNING_OBJECTIVES,
            ContextSection.KNOWLEDGE_DIGEST,
            # ContextSection.INFORMATION_REQUESTS,
            # ContextSection.SUGGESTED_NEXT_ACTIONS,
            ContextSection.COORDINATOR_CONVERSATION,
            ContextSection.ATTACHMENTS,
        ],
    )

    # Chat completion
    async with openai_client.create_client(config.service_config) as client:
        try:
            completion_args = {
                "messages": prompt.messages(),
                "model": config.request_config.openai_model,
                "max_tokens": 500,
                "temperature": 0.8,
            }
            debug["completion_args"] = openai_client.serializable(completion_args)

            # LLM call
            response = await client.chat.completions.create(
                **completion_args,
            )
            openai_client.validate_completion(response)
            debug["completion_response"] = openai_client.serializable(response.model_dump())

            # Response
            if response and response.choices and response.choices[0].message.content:
                output: str = response.choices[0].message.content
                if output:
                    await Notifications.notify(context, f"Generated invitation.\n\n{output}", debug_data=debug)
                return output
            else:
                logger.warning("Empty response from LLM while generating invitation.")

        except Exception as e:
            logger.exception(f"Failed to make OpenIA call: {e}")
            debug["error"] = str(e)

    logger.debug(f"{__name__}: {debug}")
    return "Failed to generate invitation."
