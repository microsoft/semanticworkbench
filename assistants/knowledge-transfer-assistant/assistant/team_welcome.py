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
    Geneates a welcome message for the team based on the project information.
    """
    debug: Dict[str, Any] = {}

    config = await assistant_config.get(context.assistant)

    # Get project data

    project_id = await KnowledgeTransferManager.get_share_id(context)
    if not project_id:
        raise ValueError("Project ID not found in context")

    project_data: dict[str, str] = {}

    # Briefing
    briefing = ShareStorage.read_share_brief(project_id)
    project_brief_text = ""
    if briefing:
        project_brief_text = dedent(f"""
            ### BRIEF
            **Title:** {briefing.title}
            **Description:** {briefing.description}
            """)
        project_data["briefing"] = project_brief_text

    # Goals
    project = ShareStorage.read_share(project_id)
    if project and project.learning_objectives:
        project_brief_text += "\n#### PROJECT GOALS:\n\n"
        for i, goal in enumerate(project.learning_objectives):
            completed = sum(1 for c in goal.learning_outcomes if c.achieved)
            total = len(goal.learning_outcomes)
            project_brief_text += f"{i + 1}. **{goal.name}** - {goal.description}\n"
            if goal.learning_outcomes:
                project_brief_text += f"   Progress: {completed}/{total} criteria complete\n"
                for j, criterion in enumerate(goal.learning_outcomes):
                    check = "✅" if criterion.achieved else "⬜"
                    project_brief_text += f"   {check} {criterion.description}\n"
            project_brief_text += "\n"
        project_data["goals"] = project_brief_text

    # Whiteboard
    whiteboard = ShareStorage.read_knowledge_digest(project_id)
    if whiteboard and whiteboard.content:
        whiteboard_text = dedent(f"""
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

            """)
        project_data["whiteboard"] = whiteboard_text

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
