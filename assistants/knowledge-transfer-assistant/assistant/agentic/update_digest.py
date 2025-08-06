import re

import openai_client
from semantic_workbench_api_model.workbench_model import ParticipantRole
from semantic_workbench_assistant.assistant_app import ConversationContext

from assistant.config import assistant_config
from assistant.data import KnowledgeDigest
from assistant.domain import KnowledgeDigestManager
from assistant.utils import get_current_user_id


async def update_digest(
    context: ConversationContext,
) -> KnowledgeDigest:
    """
    Automatically updates the knowledge digest by analyzing chat history.
    """
    messages = await context.get_messages()
    chat_history = messages.messages

    current_user_id = await get_current_user_id(context)
    if not current_user_id:
        raise ValueError("Could not identify current user")

    # Skip if no messages to analyze
    if not chat_history:
        raise ValueError("No chat history to analyze for knowledge digest update")

    # Format the chat history for the prompt
    chat_history_text = ""
    for msg in chat_history:
        sender_type = "User" if msg.sender and msg.sender.participant_role == ParticipantRole.user else "Assistant"
        chat_history_text += f"{sender_type}: {msg.content}\n\n"

    # Construct the knowledge digest prompt with the chat history
    config = await assistant_config.get(context.assistant)
    digest_prompt = f"""
    {config.prompt_config.knowledge_digest_update}

    <CHAT_HISTORY>
    {chat_history_text}
    </CHAT_HISTORY>
    """

    async with openai_client.create_client(config.service_config, api_version="2024-06-01") as client:
        completion = await client.chat.completions.create(
            model=config.request_config.openai_model,
            messages=[{"role": "user", "content": digest_prompt}],
            max_tokens=config.coordinator_config.max_digest_tokens,
        )

        content = completion.choices[0].message.content or ""
        digest_content = ""
        match = re.search(r"<KNOWLEDGE_DIGEST>(.*?)</KNOWLEDGE_DIGEST>", content, re.DOTALL)
        digest_content = match.group(1).strip() if match else content.strip()

    if not digest_content:
        raise ValueError("No content extracted from knowledge digest LLM analysis")

    return await KnowledgeDigestManager.update_knowledge_digest(
        context=context,
        content=digest_content,
        is_auto_generated=True,
    )
