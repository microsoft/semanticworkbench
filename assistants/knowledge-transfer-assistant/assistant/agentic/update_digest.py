import re
from typing import Any
from venv import logger

import openai_client
from assistant_extensions.attachments import AttachmentsExtension
from semantic_workbench_assistant.assistant_app import ConversationContext

from assistant.config import assistant_config
from assistant.data import InspectorTab
from assistant.domain import KnowledgeDigestManager
from assistant.domain.share_manager import ShareManager
from assistant.notifications import Notifications
from assistant.prompt_utils import ContextSection, ContextStrategy, Instructions, Prompt, add_context_to_prompt


async def update_digest(context: ConversationContext, attachments_extension: AttachmentsExtension) -> None:
    debug: dict[str, Any] = {
        "context": context.to_dict(),
    }

    config = await assistant_config.get(context.assistant)

    # Set up prompt instructions.
    instruction_text = config.prompt_config.update_knowledge_digest
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
        attachments_extension=attachments_extension,
        attachments_config=config.attachments_config,
        attachments_in_system_message=True,
        include=[
            # ContextSection.KNOWLEDGE_INFO,
            ContextSection.KNOWLEDGE_BRIEF,
            # ContextSection.TASKS,
            ContextSection.TARGET_AUDIENCE,
            ContextSection.LEARNING_OBJECTIVES,
            ContextSection.KNOWLEDGE_DIGEST,
            # ContextSection.INFORMATION_REQUESTS,
            # ContextSection.SUGGESTED_NEXT_ACTIONS,
            ContextSection.COORDINATOR_CONVERSATION,
            ContextSection.ATTACHMENTS,
        ],
    )

    async with openai_client.create_client(config.service_config, api_version="2024-06-01") as client:
        try:
            completion_args = {
                "messages": prompt.messages(),
                "model": config.request_config.openai_model,
                "max_tokens": config.coordinator_config.max_digest_tokens,
                "temperature": 0.7,
            }
            debug["completion_args"] = openai_client.serializable(completion_args)
            response = await client.chat.completions.create(**completion_args)
            openai_client.validate_completion(response)
            debug["completion_response"] = openai_client.serializable(response.model_dump())

            # Extract the knowledge digest content from the response.
            content = response.choices[0].message.content or ""
            match = re.search(r"<KNOWLEDGE_DIGEST>(.*?)</KNOWLEDGE_DIGEST>", content, re.DOTALL)
            digest_content = match.group(1).strip() if match else content
            if not digest_content:
                logger.error("No content extracted from knowledge digest LLM analysis", extra={"debug": debug})
            debug["digest_content"] = digest_content

            # Save the knowledge digest.
            await KnowledgeDigestManager.update_knowledge_digest(
                context=context,
                content=digest_content,
                is_auto_generated=True,
            )

            # Use this for debugging in the Semantic Workbench UI.
            await Notifications.notify(context, "Updated knowledge digest.", debug_data=debug)
            await Notifications.notify_state_update(
                context,
                [InspectorTab.DEBUG],
            )

        except Exception as e:
            debug["error"] = str(e)
            logger.exception(f"Failed to make OpenIA call: {e}", extra={"debug": debug})

        logger.debug(f"{__name__}: {debug}")
