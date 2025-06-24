from dataclasses import dataclass
from typing import Callable, cast

from openai import AsyncOpenAI
from openai.types.chat import (
    ChatCompletionMessageParam,
    ChatCompletionSystemMessageParam,
    ChatCompletionUserMessageParam,
)

from chat_context_toolkit.history import OpenAIHistoryMessageParam

AsyncOpenAIClientFactory = Callable[[], AsyncOpenAI]


@dataclass
class LLMArchiveSummarizerConfig:
    model: str = "gpt-4o"
    response_tokens: int = 1_000


SUMMARY_GENERATION_PROMPT = """You are summarizing portions of a conversation so they can be easily retrieved. \
You must focus on what the user role wanted, preferred, and any critical information that they shared. \
Always prefer to include information from the user than from any other role. \
Include the content from other roles only as much as necessary to provide the necessary content.
Instead of saying "you said" or "the user said", be specific and use the roles or names to indicate who said what. \
Include the key topics or things that were done.

The summary should be at most four sentences, factual, and free from making anything up or inferences that you are not completely sure about."""


async def _compute_chunk_summary(
    oai_messages: list[ChatCompletionMessageParam],
    client_factory: AsyncOpenAIClientFactory,
    llm_config: LLMArchiveSummarizerConfig,
) -> str:
    """
    Compute a summary for a chunk of messages.
    """
    conversation_text = convert_oai_messages_to_xml(oai_messages)
    summary_messages = [
        ChatCompletionSystemMessageParam(role="system", content=SUMMARY_GENERATION_PROMPT),
        ChatCompletionUserMessageParam(
            role="user",
            content=f"{conversation_text}\n\nPlease summarize the conversation above according to your instructions.",
        ),
    ]

    async with client_factory() as client:
        summary_response = await client.chat.completions.create(
            messages=summary_messages,
            model=llm_config.model,
            max_tokens=llm_config.response_tokens,
        )

    summary = summary_response.choices[0].message.content or ""
    return summary


def convert_oai_messages_to_xml(oai_messages: list[ChatCompletionMessageParam]) -> str:
    """
    Converts OpenAI messages to an XML-like formatted string.
    Example:
    <conversation filename="conversation_20250520_201521_20250520_201521.txt">
    <message role="user">
    message content here
    </message>
    <message role="assistant">
    message content here
    <toolcall name="tool_name">
    tool content here
    </toolcall>
    </message>
    <message role="tool">
    tool content here
    </message>
    <message role="user">
    <content>
    content here
    </content>
    <content>
    content here
    </content>
    </message>
    </conversation>
    """
    xml_parts = ["<conversation>"]
    for msg in oai_messages:
        role = msg.get("role", "")
        xml_parts.append(f'<message role="{role}"')

        match msg:
            case {"role": "assistant"}:
                content = msg.get("content")
                match content:
                    case str():
                        xml_parts.append(content)
                    case list():
                        for part in content:
                            if isinstance(part, dict) and part.get("type") == "text":
                                xml_parts.append(part.get("text", ""))

                tool_calls = msg.get("tool_calls", [])
                for tool_call in tool_calls:
                    if tool_call.get("type") == "function":
                        function = tool_call.get("function", {})
                        function_name = function.get("name", "unknown")
                        arguments = function.get("arguments", "")
                        xml_parts.append(f'<toolcall name="{function_name}">')
                        xml_parts.append(arguments)
                        xml_parts.append("</toolcall>")

            case {"role": "tool"}:
                content = msg.get("content")
                match content:
                    case str():
                        xml_parts.append(content)
                    case list():
                        for part in content:
                            if isinstance(part, dict) and part.get("type") == "text":
                                xml_parts.append(part.get("text", ""))

            case _:
                content = msg.get("content")
                match content:
                    case str():
                        xml_parts.append(content)
                    case list():
                        for part in content:
                            if isinstance(part, dict) and part.get("type") == "text":
                                xml_parts.append("<content>")
                                xml_parts.append(part.get("text", ""))
                                xml_parts.append("</content>")

        xml_parts.append("</message>")

    xml_parts.append("</conversation>")
    return "\n".join(xml_parts)


class LLMArchiveSummarizer:
    """
    Implementation of an archive summarizer that uses OpenAI's chat completions to summarize messages.
    """

    def __init__(self, client_factory: AsyncOpenAIClientFactory, llm_config: LLMArchiveSummarizerConfig) -> None:
        self._client_factory = client_factory
        self._llm_config = llm_config

    async def summarize(self, messages: list[OpenAIHistoryMessageParam]) -> str:
        """
        Summarize the messages for archiving.
        This function should implement the logic to summarize the messages.
        """
        summary = await _compute_chunk_summary(
            oai_messages=cast(list[ChatCompletionMessageParam], messages),
            client_factory=self._client_factory,
            llm_config=self._llm_config,
        )
        return summary
