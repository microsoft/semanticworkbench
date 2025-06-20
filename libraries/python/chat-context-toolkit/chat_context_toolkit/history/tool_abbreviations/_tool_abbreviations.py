import json
import logging
from dataclasses import dataclass, field
from typing import Any, Iterable

from openai.types.chat import (
    ChatCompletionAssistantMessageParam,
    ChatCompletionMessageToolCallParam,
    ChatCompletionToolMessageParam,
)

from .. import OpenAIHistoryMessageParam

logger = logging.getLogger("history.tool_abbreviations")


@dataclass
class Abbreviations:
    tool_call_argument_replacements: dict[str, Any] = field(default_factory=dict)
    """
    The argument names, with abbreviated values, to replace in abbreviated the assistant tool calls.
    """
    tool_message_replacement: str | None = None
    """
    The abbreviated content to replace in the tool messages. If None, the tool message will not be abbreviated.
    """


ToolAbbreviations = dict[str, Abbreviations]
"""A mapping of tool names to their abbreviations for assistant tool calls and tool messages."""


class HistoryMessageWithToolAbbreviation:
    """
    A HistoryMessageProtocol implementation that includes an abbreviated OpenAI message representation
    for tool messages and assistant messages with tool calls.
    """

    def __init__(
        self,
        id: str,
        openai_message: OpenAIHistoryMessageParam,
        tool_abbreviations: ToolAbbreviations,
        tool_name_for_tool_message: str | None = None,
    ) -> None:
        self.id = id
        self.openai_message = openai_message
        self._abbreviated_openai_message_created = False
        self._tool_abbreviations = tool_abbreviations
        self._tool_name_for_tool_message = tool_name_for_tool_message

    @property
    def abbreviated_openai_message(self) -> OpenAIHistoryMessageParam | None:
        if self._abbreviated_openai_message_created:
            return self._abbreviated_openai_message
        self._abbreviated_openai_message = abbreviate_openai_message(
            tool_name_for_tool_message=self._tool_name_for_tool_message,
            openai_message=self.openai_message,
            tool_abbreviations=self._tool_abbreviations,
        )
        self._abbreviated_openai_message_created = True
        return self._abbreviated_openai_message


def abbreviate_openai_message(
    openai_message: OpenAIHistoryMessageParam,
    tool_abbreviations: ToolAbbreviations,
    tool_name_for_tool_message: str | None = None,
) -> OpenAIHistoryMessageParam | None:
    """
    Abbreviate the OpenAI message if it is a tool message or an assistant message with tool calls.

    All other messages are left unchanged.
    """

    match openai_message:
        case {"role": "tool"}:
            if not tool_name_for_tool_message:
                logger.warning("tool_name_for_tool_call is not set for tool message: %s", openai_message)
                return openai_message
            return abbreviate_tool_message(
                tool_name=tool_name_for_tool_message,
                openai_message=openai_message,
                tool_abbreviations=tool_abbreviations,
            )

        case {"role": "assistant", "tool_calls": tool_calls}:
            return abbreviate_tool_call_message(openai_message, tool_calls, tool_abbreviations)

    return openai_message


def abbreviate_tool_message(
    tool_name: str,
    openai_message: ChatCompletionToolMessageParam,
    tool_abbreviations: ToolAbbreviations,
) -> OpenAIHistoryMessageParam:
    if tool_name not in tool_abbreviations:
        # no abbreviations for this tool, return the original message
        return openai_message

    content = tool_abbreviations[tool_name].tool_message_replacement
    if content is None:
        # no abbreviation for the tool message, return the original message
        return openai_message

    abbreviation_is_shorter = len(content) < len(str(openai_message.get("content", "")))
    if not abbreviation_is_shorter:
        # only abbreviate if the replacement content is shorter than the original content
        return openai_message

    # return a new message with the abbreviated content
    abbreviated_message = openai_message.copy()
    abbreviated_message["content"] = content
    return abbreviated_message


def abbreviate_tool_call_message(
    openai_message: ChatCompletionAssistantMessageParam,
    tool_calls: Iterable[ChatCompletionMessageToolCallParam],
    tool_abbreviations: ToolAbbreviations,
) -> OpenAIHistoryMessageParam:
    abbreviated_tool_calls: list[ChatCompletionMessageToolCallParam] = []

    for tool_call in tool_calls:
        function = tool_call.get("function", {})
        tool_name = function.get("name")

        try:
            arguments = json.loads(function.get("arguments", "{}"))
        except (json.JSONDecodeError, ValueError):
            logger.exception("failed to parse arguments for tool call: %s, skipping abbreviation", tool_call)
            abbreviated_tool_calls.append(tool_call)
            continue

        if tool_name not in tool_abbreviations:
            # no abbreviations for this tool, return the original message
            abbreviated_tool_calls.append(tool_call)
            continue

        arguments.update(tool_abbreviations[tool_name].tool_call_argument_replacements)

        # append a tool call with the abbreviated arguments
        abbreviated_tool_call = tool_call.copy()
        abbreviated_tool_call["function"]["arguments"] = json.dumps(arguments)
        abbreviated_tool_calls.append(abbreviated_tool_call)

    abbreviated_message = openai_message.copy()
    abbreviated_message["tool_calls"] = abbreviated_tool_calls
    return abbreviated_message
