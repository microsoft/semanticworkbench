# Copyright (c) Microsoft. All rights reserved.

import logging
from hashlib import md5
from typing import Awaitable, Callable

from openai.types.chat import (
    ChatCompletionMessageParam,
)
from pydantic import BaseModel
from semantic_workbench_api_model import workbench_model
from semantic_workbench_assistant.assistant_app import (
    AssistantAppProtocol,
    AssistantConversationInspectorStateDataModel,
    ConversationContext,
)

from assistant.config import AssistantConfigModel
from assistant.types import FileManagerData

logger = logging.getLogger(__name__)


class ContextManagementTelemetry(BaseModel):
    total_context_tokens: int = 0
    system_prompt_tokens: int = 0
    tool_tokens: int = 0
    message_tokens: int = 0

    system_prompt: str = ""
    final_messages: list[ChatCompletionMessageParam] = []

    file_manager_data: FileManagerData = FileManagerData()

    def construct_markdown_str(self) -> str:
        if self.total_context_tokens == 0:
            return "**Debug use only. Send a message to see the context management output for the final step of the conversation.**"

        markdown_str = "## Key Metrics\n"
        markdown_str += f"* **Total tokens sent to LLM:** {self.total_context_tokens}\n"
        markdown_str += f"* **System prompt tokens:** {self.system_prompt_tokens}\n"
        markdown_str += f"* **Tool tokens:** {self.tool_tokens}\n"
        markdown_str += f"* **Message tokens after context management:** {self.message_tokens}\n\n"

        markdown_str += "## System Prompt\n"
        system_prompt = self.system_prompt.strip().replace("```", "\\`\\`\\`")
        markdown_str += f"```markdown\n{system_prompt}\n```\n\n"

        def format_content(content: str, max_chars: int = 200) -> str:
            """Helper to format content by truncating, escaping backticks, and removing newlines."""
            if len(content) > max_chars:
                content = content[:max_chars] + "... truncated"
            return content.replace("```", "\\`\\`\\`").replace("\n", " ").replace("\r", " ")

        # Convert messages to markdown
        messages_markdown = ""
        max_content_chars = 200
        for i, msg in enumerate(self.final_messages[1:]):
            role = msg.get("role", "")
            messages_markdown += f"### Message {i + 1} - {role.capitalize()}\n\n"

            if role == "assistant":
                content = msg.get("content")
                if content:
                    if isinstance(content, str):
                        content_formatted = format_content(content, max_content_chars)
                        messages_markdown += f"{content_formatted}\n"
                    elif isinstance(content, list):
                        for part in content:
                            if isinstance(part, dict) and part.get("type") == "text":
                                text_formatted = format_content(part.get("text", ""), max_content_chars)
                                messages_markdown += f"{text_formatted}\n"

                tool_calls = msg.get("tool_calls", [])
                if tool_calls:
                    messages_markdown += "**Tool Calls:**\n"
                    for tool_call in tool_calls:
                        if tool_call.get("type") == "function":
                            function = tool_call.get("function", {})
                            function_name = function.get("name", "unknown")
                            arguments = format_content(function.get("arguments", "{}"), max_content_chars)
                            messages_markdown += f"\n- **{function_name}**: {arguments}\n"

            elif role == "tool":
                tool_call_id = msg.get("tool_call_id", "")
                messages_markdown += f"**Tool Response** (ID: {tool_call_id})\n"
                content = msg.get("content")
                if isinstance(content, str):
                    content_formatted = format_content(content, max_content_chars)
                    messages_markdown += f"- {content_formatted}\n"
                elif isinstance(content, list):
                    for part in content:
                        if isinstance(part, dict) and part.get("type") == "text":
                            text_formatted = format_content(part.get("text", ""), max_content_chars)
                            messages_markdown += f"- {text_formatted}\n"

            elif role in ["user", "system", "developer"]:
                content = msg.get("content")
                if isinstance(content, str):
                    content_formatted = format_content(content, max_content_chars)
                    messages_markdown += f"{content_formatted}\n\n"
                elif isinstance(content, list):
                    for j, part in enumerate(content):
                        if isinstance(part, dict) and part.get("type") == "text":
                            if len(content) > 1:
                                messages_markdown += f"**Part {j + 1}:**\n"
                            text_formatted = format_content(part.get("text", ""), max_content_chars)
                            messages_markdown += f"{text_formatted}\n"

            messages_markdown += "\n\n"

        markdown_str += "## Conversation Messages\n"
        markdown_str += f"```markdown\n{messages_markdown}```\n"

        if self.file_manager_data.file_data:
            sorted_files = sorted(
                self.file_manager_data.file_data.items(),
                key=lambda x: x[1].recency_probability * 0.25 + x[1].relevance_probability * 0.75,
                reverse=True,
            )
            file_scores_markdown = "| Score | File | Recency Probability | Relevance Probability | Brief Reasoning |\n"
            file_scores_markdown += "|-------|------|---------------------|----------------------|----------------|\n"
            for filename, file_relevance in sorted_files:
                score = file_relevance.recency_probability * 0.25 + file_relevance.relevance_probability * 0.75
                safe_filename = filename.replace("|", "\\|")
                safe_reasoning = file_relevance.brief_reasoning.replace("|", "\\|").replace("\n", " ")
                file_scores_markdown += f"| {score:.2f} | {safe_filename} | {file_relevance.recency_probability:.2f} | {file_relevance.relevance_probability:.2f} | {safe_reasoning} |\n"

            markdown_str += "## File Relevance Scores\n"
            markdown_str += f"```markdown\n{file_scores_markdown}```\n"

        return markdown_str


class ContextManagementInspector:
    def __init__(
        self,
        app: AssistantAppProtocol,
        config_provider: Callable[[ConversationContext], Awaitable[AssistantConfigModel]],
        display_name: str = "Debug: Context Management",
        description: str = "",
    ) -> None:
        self._state_id = md5(
            (type(self).__name__ + "_" + display_name).encode("utf-8"),
            usedforsecurity=False,
        ).hexdigest()
        self._display_name = display_name
        self._description = description
        self._telemetry: dict[str, ContextManagementTelemetry] = {}
        self._config_provider = config_provider

        app.add_inspector_state_provider(state_id=self._state_id, provider=self)

    @property
    def state_id(self) -> str:
        return self._state_id

    @property
    def display_name(self) -> str:
        return self._display_name

    @property
    def description(self) -> str:
        return self._description

    async def is_enabled(self, context: ConversationContext) -> bool:
        config = await self._config_provider(context)
        return config.additional_debug_info

    def get_telemetry(self, conversation_id: str) -> ContextManagementTelemetry:
        """Get or create telemetry for a conversation."""
        if conversation_id not in self._telemetry:
            self._telemetry[conversation_id] = ContextManagementTelemetry()
        return self._telemetry[conversation_id]

    def reset_telemetry(self, conversation_id: str) -> ContextManagementTelemetry:
        """Reset telemetry for a conversation and return the new instance."""
        self._telemetry[conversation_id] = ContextManagementTelemetry()
        return self._telemetry[conversation_id]

    async def get(self, context: ConversationContext) -> AssistantConversationInspectorStateDataModel:
        telemetry = self.get_telemetry(context.id)

        return AssistantConversationInspectorStateDataModel(
            data={
                "markdown_content": telemetry.construct_markdown_str(),
                "filename": "",
                "readonly": True,
            }
        )

    async def update_state(
        self, context: ConversationContext, telemetry: ContextManagementTelemetry | None = None
    ) -> None:
        if telemetry is not None:
            self._telemetry[context.id] = telemetry

        # Send an event to update the UI
        await context.send_conversation_state_event(
            workbench_model.AssistantStateEvent(
                state_id=self._state_id,
                event="updated",
                state=None,
            )
        )
