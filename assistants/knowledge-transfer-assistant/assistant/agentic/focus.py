from typing import Any

import openai_client
from assistant_extensions.attachments import AttachmentsExtension
from pydantic import BaseModel
from semantic_workbench_assistant.assistant_app import ConversationContext

from assistant.config import assistant_config
from assistant.data import InspectorTab
from assistant.domain.tasks_manager import TasksManager
from assistant.logging import logger
from assistant.notifications import Notifications
from assistant.prompt_utils import (
    ContextStrategy,
    DataContext,
    Instructions,
    Prompt,
)
from assistant.utils import load_text_include


async def focus(context: ConversationContext, attachments_extension: AttachmentsExtension) -> None:
    debug: dict[str, Any] = {
        "context": context.to_dict(),
    }

    config = await assistant_config.get(context.assistant)

    # Set up prompt instructions.
    instruction_text = load_text_include("focus.md")
    instructions = Instructions(instruction_text)
    prompt = Prompt(
        instructions=instructions,
        context_strategy=ContextStrategy.MULTI,
    )

    tasks = await TasksManager.get_tasks(context)
    if tasks:
        tasks_data = "\n\n".join("- " + thought for thought in tasks)
        prompt.contexts.append(
            DataContext(
                "Consulting Tasks",
                tasks_data,
                "The consultant's current task list for the knowledge transfer consulting project.",
            )
        )
    else:
        prompt.contexts.append(
            DataContext(
                "Consulting Tasks",
                "[]",
                "The consultant has no current tasks for the knowledge transfer consulting project.",
            )
        )

    class Output(BaseModel):
        """Output class to hold the generated tasks."""

        reasoning: str  # Reasoning behind how you are focusing the task list.
        focused_tasks: list[str]  # Focused task list for the knowledge transfer consultant.

    # Chat completion
    async with openai_client.create_client(config.service_config) as client:
        try:
            completion_args = {
                "messages": prompt.messages(),
                "model": config.request_config.openai_model,
                "max_tokens": 500,
                "temperature": 0.8,
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
                if output.focused_tasks:
                    await TasksManager.set_task_list(context, output.focused_tasks)
                    await Notifications.notify(context, "Focused the task list.", debug_data=debug)
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
