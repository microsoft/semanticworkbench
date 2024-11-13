from openai import AsyncAzureOpenAI, AsyncOpenAI
from openai_client.chat_driver import ChatDriver, ChatDriverConfig, InMemoryMessageHistoryProvider
from openai_client.messages import format_with_liquid

from ..document_skill import Outline, Paper


async def get_user_feedback_for_outline_decision(
    session_id: str,
    open_ai_client: AsyncOpenAI | AsyncAzureOpenAI,
    chat_history: str,
    outline_versions: list[Outline] = [],
    paper_versions: list[Paper] = [],
    user_feedback: str | None = None,
    outline: bool = False,
):
    history = InMemoryMessageHistoryProvider(formatter=format_with_liquid)

    if outline:
        history.append_system_message(
            (
                "Use the user's most recent feedback to determine if the user wants to iterate further on the"
                " provided outline [ITERATE], or if the user is ready to move on to drafting a paper from the"
                " provided outline [CONTINUE]. Based on the user's feedback on the provided outline, determine if"
                " the user wants to [ITERATE], [CONTINUE], or [QUIT]. Reply with ONLY [ITERATE], [CONTINUE], or [QUIT]."
            )
        )
    else:
        history.append_system_message(
            (
                "You are an AI assistant that helps draft outlines for a future flushed-out document."
                " You use the user's most recent feedback to determine if the user wants to iterate further on the"
                " provided draft content [ITERATE], or if the user is ready to move on to drafting new additional content"
                " [CONTINUE]. Based on the user's feedback on the provided drafted content, determine if"
                " the user wants to [ITERATE], [CONTINUE], or [QUIT]. Reply with ONLY [ITERATE], [CONTINUE], or [QUIT]."
            )
        )

    history.append_system_message("<CHAT_HISTORY>{{chat_history}}</CHAT_HISTORY>", {"chat_history": chat_history})

    if len(outline_versions):
        last_outline_content = outline_versions[-1].content
        if outline:
            history.append_system_message(
                "<EXISTING_OUTLINE>{{outline}}</EXISTING_OUTLINE>", {"outline": last_outline_content}
            )
        else:
            history.append_system_message(
                "<APPROVED_OUTLINE>{{outline}}</APPROVED_OUTLINE>", {"outline": last_outline_content}
            )

    if not outline:
        if paper_versions:
            full_paper_content = ""
            for content in paper_versions[-1].contents:
                full_paper_content += content.content
            history.append_system_message(
                "<EXISTING_CONTENT>{{content}}</EXISTING_CONTENT>", {"content": full_paper_content}
            )

    if user_feedback is not None:
        history.append_system_message(
            "<USER_FEEDBACK>{{user_feedback}}</USER_FEEDBACK>", {"user_feedback": user_feedback}
        )

    config = ChatDriverConfig(
        openai_client=open_ai_client,
        model="gpt-3.5-turbo",
        message_provider=history,
    )

    chat_driver = ChatDriver(config)
    return await chat_driver.respond()
