"""
Analysis and detection functions for the knowledge transfer assistant.

This module contains functions for analyzing messages and knowledge transfer
share content to detect specific conditions, such as information request needs.
"""

from textwrap import dedent
from typing import Any

import openai_client
from openai.types.chat import ChatCompletionMessageParam
from semantic_workbench_assistant.assistant_app import ConversationContext

from assistant.config import assistant_config
from assistant.domain.share_manager import ShareManager
from assistant.logging import logger
from assistant.utils import load_text_include


async def generate_team_welcome_message(
    context: ConversationContext,
) -> tuple[str, dict[str, Any]]:
    """
    Generates a welcome message for the team based on the knowledge transfer information.
    """
    debug: dict[str, Any] = {}

    config = await assistant_config.get(context.assistant)

    try:
        share = await ShareManager.get_share(context)
    except Exception as e:
        logger.error(f"Failed to get share for welcome message generation: {e}")
        return config.team_config.default_welcome_message, debug

    share_data: dict[str, str] = {}

    # Knowledge Brief
    briefing = share.brief
    brief_text = ""
    if briefing:
        brief_text = dedent(f"""
            ### Knowledge Brief

            #### {briefing.title}

            {briefing.content}
            """)
        share_data["briefing"] = brief_text

    # Learning Objectives
    if share and share.learning_objectives:
        brief_text += "\n#### LEARNING OBJECTIVES:\n\n"

        for i, objective in enumerate(share.learning_objectives):
            brief_text += f"{i + 1}. **{objective.name}** - {objective.description}\n"
            if objective.learning_outcomes:
                for criterion in objective.learning_outcomes:
                    check = "⬜"
                    brief_text += f"   {check} {criterion.description}\n"
            brief_text += "\n"
        share_data["learning_objectives"] = brief_text

    # Knowledge Digest
    knowledge_digest = share.digest
    if knowledge_digest and knowledge_digest.content:
        knowledge_digest_text = load_text_include("knowledge_digest_instructions.txt") + dedent(f"""
            KNOWLEDGE DIGEST CONTENT:
            ```markdown
            {knowledge_digest.content}
            ```

            """)
        share_data["knowledge_digest"] = knowledge_digest_text
        share_data["knowledge_digest"] = knowledge_digest_text

    try:
        # Chat completion
        async with openai_client.create_client(config.service_config) as client:
            share_info = "\n\n## KNOWLEDGE SHARE INFORMATION\n\n" + "\n".join(share_data.values())

            instructions = f"{config.prompt_config.welcome_message_generation}\n\n{share_info}"
            messages: list[ChatCompletionMessageParam] = [
                {"role": "system", "content": instructions},
            ]

            completion_args = {
                "model": config.request_config.openai_model,
                "messages": messages,
                "max_tokens": 500,
                "temperature": 0.7,  # Low temperature for more consistent analysis
            }
            debug["completion_args"] = openai_client.serializable(completion_args)

            # LLM call
            response = await client.chat.completions.create(
                **completion_args,
            )
            debug["completion_response"] = response.model_dump()

        # Response
        if response and response.choices and response.choices[0].message.content:
            return response.choices[0].message.content, debug
        else:
            logger.warning("Empty response from LLM for welcome message generation")
            return config.team_config.default_welcome_message, debug

    except Exception as e:
        logger.error(f"Failed to generate welcome message: {e}")
        debug["error"] = str(e)
        return config.team_config.default_welcome_message, debug
