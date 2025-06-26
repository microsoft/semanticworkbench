import datetime
import logging
from typing import Callable

from attr import dataclass
from openai import AsyncOpenAI
from openai.types.chat import (
    ChatCompletionContentPartImageParam,
    ChatCompletionContentPartTextParam,
    ChatCompletionSystemMessageParam,
    ChatCompletionUserMessageParam,
)
from semantic_workbench_assistant.assistant_app import ConversationContext

from ._model import Attachment, AttachmentSummary, Summarizer
from ._shared import original_to_attachment_filename, summary_drive_for_context

logger = logging.getLogger("assistant_extensions.attachments")


async def get_attachment_summary(context: ConversationContext, filename: str) -> AttachmentSummary:
    """
    Get the summary of the attachment from the summary drive.
    If the summary file does not exist, returns None.
    """
    drive = summary_drive_for_context(context)

    try:
        return drive.read_model(AttachmentSummary, original_to_attachment_filename(filename))

    except FileNotFoundError:
        # If the summary file does not exist, return None
        return AttachmentSummary(
            summary="",
        )


async def summarize_attachment_task(
    context: ConversationContext, summarizer: Summarizer, attachment: Attachment
) -> None:
    """
    Summarize the attachment and save the summary to the summary drive.
    """

    logger.info("summarizing attachment; filename: %s", attachment.filename)

    summary = await summarizer.summarize(attachment=attachment)

    attachment_summary = AttachmentSummary(summary=summary, updated_datetime=datetime.datetime.now(datetime.UTC))

    drive = summary_drive_for_context(context)
    # Save the summary
    drive.write_model(attachment_summary, original_to_attachment_filename(attachment.filename))

    logger.info("summarization of attachment complete; filename: %s", attachment.filename)


@dataclass
class LLMConfig:
    client_factory: Callable[[], AsyncOpenAI]
    model: str
    max_response_tokens: int

    file_summary_system_message: str = """You will be provided the content of a file.
It is your goal to factually, accurately, and concisely summarize the content of the file.
You must do so in less than 3 sentences or 100 words."""


class LLMFileSummarizer(Summarizer):
    def __init__(self, llm_config: LLMConfig) -> None:
        self.llm_config = llm_config

    async def summarize(self, attachment: Attachment) -> str:
        llm_config = self.llm_config

        content_param = ChatCompletionContentPartTextParam(type="text", text=attachment.content)
        if attachment.content.startswith("data:image/"):
            # If the content is an image, we need to provide a different message format
            content_param = ChatCompletionContentPartImageParam(
                type="image_url",
                image_url={"url": attachment.content},
            )

        chat_message_params = [
            ChatCompletionSystemMessageParam(role="system", content=llm_config.file_summary_system_message),
            ChatCompletionUserMessageParam(
                role="user",
                content=[
                    ChatCompletionContentPartTextParam(
                        type="text",
                        text=f"Filename: {attachment.filename}",
                    ),
                    content_param,
                    ChatCompletionContentPartTextParam(
                        type="text",
                        text="Please concisely and accurately summarize the file contents.",
                    ),
                ],
            ),
        ]

        async with llm_config.client_factory() as client:
            summary_response = await client.chat.completions.create(
                messages=chat_message_params,
                model=llm_config.model,
                max_tokens=llm_config.max_response_tokens,
            )

        return summary_response.choices[0].message.content or ""
