"""
Analysis and detection functions for the project assistant.

This module contains functions for analyzing messages and project content
to detect specific conditions, such as information request needs.
"""

from textwrap import dedent
from typing import Any, Dict, List

import openai_client
from openai.types.chat import ChatCompletionMessageParam
from semantic_workbench_assistant.assistant_app import ConversationContext

from assistant.manager import KnowledgeTransferManager
from assistant.storage import ShareStorage

from .config import assistant_config
from .logging import logger


async def generate_team_welcome_message(context: ConversationContext) -> tuple[str, dict[str, Any]]:
    """
    Generates a welcome message for the team based on the project information.
    """
    debug: Dict[str, Any] = {}

    config = await assistant_config.get(context.assistant)

    # Get project data

    project_id = await KnowledgeTransferManager.get_share_id(context)
    if not project_id:
        raise ValueError("Project ID not found in context")

    project_data: dict[str, str] = {}

    # Briefing
    briefing = ShareStorage.read_knowledge_brief(project_id)
    brief_text = ""
    if briefing:
        brief_text = dedent(f"""
            ### BRIEF
            **Title:** {briefing.title}
            **Description:** {briefing.content}
            """)
        project_data["briefing"] = brief_text

    # Learning Objectives
    share = ShareStorage.read_share(project_id)
    if share and share.learning_objectives:
        brief_text += "\n#### LEARNING OBJECTIVES:\n\n"
        conversation_id = str(context.id)

        # Show team member's personal progress (initially 0)
        if conversation_id in share.team_conversations:
            achieved_personal, total_personal = share.get_completion_for_conversation(conversation_id)
            progress_pct = int((achieved_personal / total_personal * 100)) if total_personal > 0 else 0
            brief_text += (
                f"**My Progress:** {achieved_personal}/{total_personal} outcomes achieved ({progress_pct}%)\n\n"
            )

        for i, objective in enumerate(share.learning_objectives):
            brief_text += f"{i + 1}. **{objective.name}** - {objective.description}\n"
            if objective.learning_outcomes:
                for j, criterion in enumerate(objective.learning_outcomes):
                    # Show team member's achievement status for each outcome
                    achieved_by_me = share.is_outcome_achieved_by_conversation(criterion.id, conversation_id)
                    check = "✅" if achieved_by_me else "⬜"
                    brief_text += f"   {check} {criterion.description}\n"
            brief_text += "\n"
        project_data["learning_objectives"] = brief_text

    # Whiteboard
    knowledge_digest = ShareStorage.read_knowledge_digest(project_id)
    if knowledge_digest and knowledge_digest.content:
        knowledge_digest_text = dedent(f"""
            ### ASSISTANT KNOWLEDGE DIGEST - KEY PROJECT KNOWLEDGE
            The knowledge digest contains critical project information that has been automatically extracted from previous conversations.
            It serves as a persistent memory of important facts, decisions, and context that you should reference when responding.

            Key characteristics of this knowledge digest:
            - It contains the most essential information about the project that should be readily available
            - It has been automatically curated to focus on high-value content relevant to the project
            - It is maintained and updated as the conversation progresses
            - It should be treated as a trusted source of contextual information for this project

            When using the knowledge digest:
            - Prioritize this information when addressing questions or providing updates
            - Reference it to ensure consistency in your responses across the conversation
            - Use it to track important details that might otherwise be lost in the conversation history

            KNOWLEDGE DIGEST CONTENT:
            ```markdown
            {knowledge_digest.content}
            ```

            """)
        project_data["knowledge_digest"] = knowledge_digest_text

    try:
        # Chat completion
        async with openai_client.create_client(config.service_config) as client:
            project_info = "\n\n## CURRENT PROJECT INFORMATION\n\n" + "\n".join(project_data.values())

            instructions = f"{config.prompt_config.welcome_message_generation}\n\n{project_info}"
            messages: List[ChatCompletionMessageParam] = [
                {"role": "system", "content": instructions},
            ]

            completion_args = {
                "model": config.request_config.openai_model,
                "messages": messages,
                "max_tokens": 500,
                "temperature": 0.7,  # Low temperature for more consistent analysis
            }
            debug["completion_args"] = openai_client.make_completion_args_serializable(completion_args)

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
