from openai import AsyncAzureOpenAI, AsyncOpenAI
from openai_client.chat_driver import ChatDriver, ChatDriverConfig, InMemoryMessageHistoryProvider
from openai_client.messages import format_with_liquid

from ..document_skill import Outline


async def draft_outline(
    session_id: str,
    open_ai_client: AsyncOpenAI | AsyncAzureOpenAI,
    chat_history: str,
    attachments: list,
    outline_versions: list[Outline] = [],
    user_feedback: str | None = None,
):
    history = InMemoryMessageHistoryProvider(formatter=format_with_liquid)

    await history.append_system_message(
        (
            "Generate an outline for the document, including title. The outline should include the key points that will"
            " be covered in the document. Consider the attachments, the rationale for why they were uploaded, and the"
            " conversation that has taken place. The outline should be a hierarchical structure with multiple levels of"
            " detail, and it should be clear and easy to understand. The outline should be generated in a way that is"
            " consistent with the document that will be generated from it."
        )
    )

    await history.append_system_message("<CHAT_HISTORY>{{chat_history}}</CHAT_HISTORY>", {"chat_history": chat_history})

    for item in attachments:
        await history.append_system_message(
            "<ATTACHMENT><FILENAME>{{item.filename}}</FILENAME><CONTENT>{{item.content}}</CONTENT></ATTACHMENT>",
            {"item": item},
        )

    if len(outline_versions):
        last_outline = outline_versions[-1]
        await history.append_system_message(
            "<EXISTING_OUTLINE>{{last_outline}}</EXISTING_OUTLINE>", {"last_outline": last_outline}
        )

    if user_feedback is not None:
        await history.append_system_message(
            "<USER_FEEDBACK>{{user_feedback}}</USER_FEEDBACK>", {"user_feedback": user_feedback}
        )

    config = ChatDriverConfig(
        openai_client=open_ai_client,
        model="gpt-3.5-turbo",
        message_provider=history,
    )

    chat_driver = ChatDriver(config)
    return await chat_driver.respond()
