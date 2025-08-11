from typing import Any

import openai_client
from assistant_extensions.attachments import AttachmentsExtension
from pydantic import BaseModel
from semantic_workbench_assistant.assistant_app import ConversationContext

from assistant.config import assistant_config
from assistant.data import InspectorTab
from assistant.domain.share_manager import ShareManager
from assistant.domain.tasks_manager import TasksManager
from assistant.logging import logger
from assistant.notifications import Notifications
from assistant.prompt_utils import (
    ContextSection,
    ContextStrategy,
    Instructions,
    Prompt,
    add_context_to_prompt,
)
from assistant.utils import load_text_include


async def detect_coordinator_actions(context: ConversationContext, attachments_extension: AttachmentsExtension) -> None:
    debug: dict[str, Any] = {
        "context": context.to_dict(),
    }

    config = await assistant_config.get(context.assistant)

    # Set up prompt instructions.
    instruction_text = load_text_include("detect_coordinator_actions.md")
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
            ContextSection.KNOWLEDGE_INFO,
            ContextSection.KNOWLEDGE_BRIEF,
            ContextSection.TASKS,
            ContextSection.TARGET_AUDIENCE,
            ContextSection.LEARNING_OBJECTIVES,
            ContextSection.KNOWLEDGE_DIGEST,
            ContextSection.INFORMATION_REQUESTS,
            # ContextSection.SUGGESTED_NEXT_ACTIONS,
            ContextSection.COORDINATOR_CONVERSATION,
            ContextSection.ATTACHMENTS,
        ],
    )

    class Output(BaseModel):
        """Output class to hold the additional tasks."""

        tasks: list[
            str
        ]  # Additional tasks that should be completed. If there are no additional tasks needed, this will be an empty list. #noqa: E501

    # Chat completion
    async with openai_client.create_client(config.service_config) as client:
        try:
            completion_args = {
                "messages": prompt.messages(),
                "model": config.request_config.openai_model,
                "max_tokens": 500,
                "temperature": 0.7,
                "response_format": Output,
            }
            debug["completion_args"] = openai_client.serializable(completion_args)

            # LLM call
            response = await client.beta.chat.completions.parse(
                **completion_args,
            )
            openai_client.validate_completion(response)
            debug["completion_response"] = openai_client.serializable(response.model_dump())

            # Response
            if response and response.choices and response.choices[0].message.parsed:
                output: Output = response.choices[0].message.parsed
                if output.tasks:
                    await TasksManager.add_tasks(context, output.tasks)
                    await Notifications.notify(
                        context, f"Added {len(output.tasks)} tasks related to the process.", debug_data=debug
                    )
                    await Notifications.notify_state_update(
                        context,
                        [InspectorTab.DEBUG],
                    )
            else:
                logger.warning("Empty response from LLM for welcome message generation")

        except Exception as e:
            logger.exception(f"Failed to make OpenIA call: {e}")
            debug["error"] = str(e)

    logger.debug(f"{__name__}: {debug}")
