from openai import AsyncAzureOpenAI, AsyncOpenAI
from openai_client.chat_driver import ChatDriver, ChatDriverConfig, InMemoryMessageHistoryProvider
from openai_client.messages import format_with_liquid

from ..document_skill import Outline, Paper


async def draft_content(
    session_id: str,
    open_ai_client: AsyncOpenAI | AsyncAzureOpenAI,
    chat_history: str,
    attachments: list,
    outline_versions: list[Outline] = [],
    paper_versions: list[Paper] = [],
    user_feedback: str | None = None,
    decision: str | None = None,
):
    history = InMemoryMessageHistoryProvider(formatter=format_with_liquid)

    if decision == "[ITERATE]":
        history.append_system_message(
            (
                "Following the structure of the outline, iterate on the currently drafted page of the"
                " document. It's more important to maintain an appropriately useful level of detail. "
                " After this page is iterated upon, the system will follow up"
                " and ask for the next page."
            )
        )

    else:
        history.append_system_message(
            (
                "Following the structure of the outline, create the content for the next (or first) page of the"
                " document - don't try to create the entire document in one pass nor wrap it up too quickly, it will be a"
                " multi-page document so just create the next page. It's more important to maintain"
                " an appropriately useful level of detail. After this page is generated, the system will follow up"
                " and ask for the next page. If you have already generated all the pages for the"
                " document as defined in the outline, return empty content."
            )
        )

    history.append_system_message("<CHAT_HISTORY>{{chat_history}}</CHAT_HISTORY>", {"chat_history": chat_history})

    for item in attachments:
        history.append_system_message(
            "<ATTACHMENT><FILENAME>{{item.filename}}</FILENAME><CONTENT>{{item.content}}</CONTENT></ATTACHMENT>",
            {"item": item},
        )

    if outline_versions:
        last_outline = outline_versions[-1]
        history.append_system_message(
            "<APPROVED_OUTLINE>{{last_outline}}</APPROVED_OUTLINE>", {"last_outline": last_outline}
        )

    if paper_versions:
        if decision == "[ITERATE]" and user_feedback:
            content = paper_versions[-1].contents[-1].content
            history.append_system_message("<EXISTING_CONTENT>{{content}}</EXISTING_CONTENT>", {"content": content})
            history.append_system_message(
                "<USER_FEEDBACK>{{user_feedback}}</USER_FEEDBACK>", {"user_feedback": user_feedback}
            )
        else:
            full_content = ""
            for content in paper_versions[-1].contents:
                full_content += content.content
            history.append_system_message("<EXISTING_CONTENT>{{content}}</EXISTING_CONTENT>", {"content": full_content})

    config = ChatDriverConfig(
        openai_client=open_ai_client,
        model="gpt-3.5-turbo",
        message_provider=history,
    )

    chat_driver = ChatDriver(config)
    return await chat_driver.respond()
