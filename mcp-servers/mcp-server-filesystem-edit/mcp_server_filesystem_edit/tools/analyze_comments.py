import json
import logging

import pendulum
from mcp.server.fastmcp import Context
from mcp_extensions.llm.chat_completion import chat_completion
from mcp_extensions.llm.helpers import compile_messages
from mcp_extensions.llm.llm_types import ChatCompletionRequest, MessageT, UserMessage

from mcp_server_filesystem_edit import settings
from mcp_server_filesystem_edit.prompts.analyze_comments import COMMENT_ANALYSIS_MESSAGES, COMMENT_ANALYSIS_SCHEMA
from mcp_server_filesystem_edit.tools.helpers import format_chat_history
from mcp_server_filesystem_edit.types import AnalyzeCommentsOutput, CustomContext, EditTelemetry, FileOpRequest

logger = logging.getLogger(__name__)


class CommonAnalyzeComments:
    def __init__(self) -> None:
        self.telemetry = EditTelemetry()

    async def construct_analyze_comments_prompt(self, request: FileOpRequest) -> list[MessageT]:
        chat_history = ""
        if request.request_type == "dev" and isinstance(request.context, CustomContext):
            chat_history = format_chat_history(request.context.chat_history)

        context = ""
        if request.request_type == "dev" and isinstance(request.context, CustomContext):
            context = request.context.additional_context

        comments_messages = compile_messages(
            messages=COMMENT_ANALYSIS_MESSAGES,
            variables={
                "knowledge_cutoff": "2023-10",
                "current_date": pendulum.now().format("YYYY-MM-DD"),
                "context": context,
                "document": request.file_content,
                "chat_history": chat_history,
            },
        )
        return comments_messages

    async def get_response(self, request: FileOpRequest, messages: list[MessageT]) -> dict | None:
        if request.request_type == "mcp" and isinstance(request.context, Context):
            mcp_messages = [messages[0]]  # Developer message
            mcp_messages.append(UserMessage(content=json.dumps({"variable": "attachment_messages"})))
            mcp_messages.append(UserMessage(content=json.dumps({"variable": "history_messages"})))
            mcp_messages.append(messages[3])  # Document message
            analysis_response = await chat_completion(
                request=ChatCompletionRequest(
                    messages=mcp_messages,
                    model="gpt-4o",
                    max_completion_tokens=8000,
                    temperature=0.5,
                    structured_outputs=COMMENT_ANALYSIS_SCHEMA,
                ),
                provider="mcp",
                client=request.context,  # type: ignore
            )
        elif request.request_type == "dev":
            analysis_response = await chat_completion(
                request=ChatCompletionRequest(
                    messages=messages,
                    model="gpt-4o",
                    max_completion_tokens=8000,
                    temperature=0.5,
                    structured_outputs=COMMENT_ANALYSIS_SCHEMA,
                ),
                provider="azure_openai",
                client=request.chat_completion_client,  # type: ignore
            )
        else:
            raise ValueError(f"Invalid request type: {request.request_type}")

        self.telemetry.convert_latency = analysis_response.response_duration
        comment_analysis = analysis_response.choices[0].json_message
        logger.info(f"Comment analysis response:\n{comment_analysis}")
        return comment_analysis

    async def convert_to_instructions(self, json_message: dict) -> tuple[str, str]:
        edit_instructions = ""
        assistant_hints = ""
        if json_message:
            for comment in json_message.get("comment_analysis", []):
                comment_id = comment.get("comment_id", None)
                if comment_id is None:
                    continue
                output_message = comment.get("output_message", None)
                if output_message is None:
                    continue
                if comment.get("is_actionable", False) and not comment.get("is_addressed", True):
                    edit_str = f'To address the comment "{comment_id}" at location, please do the following:'
                    edit_instructions += f"{edit_str}\n{output_message}\n\n"
                elif comment.get("is_actionable", False):
                    assistant_str = f'To address the comment "{comment_id}" at location:'
                    assistant_hints += f"{assistant_str}\n{output_message}\n\n"

        if edit_instructions:
            edit_instructions = f"{settings.feedback_tool_prefix}{edit_instructions}"
            edit_instructions = edit_instructions.strip()
        if assistant_hints:
            assistant_hints = f"{settings.feedback_tool_prefix}{assistant_hints}"
            assistant_hints = assistant_hints.strip()

        return edit_instructions, assistant_hints

    async def run(self, request: FileOpRequest) -> AnalyzeCommentsOutput:
        analyze_comments_messages = await self.construct_analyze_comments_prompt(request)
        response = await self.get_response(request, analyze_comments_messages)
        edit_instructions, assistant_hints = "", ""
        if response:
            edit_instructions, assistant_hints = await self.convert_to_instructions(response)

        output = AnalyzeCommentsOutput(
            edit_instructions=edit_instructions,
            assistant_hints=assistant_hints,
            json_message=response,
        )
        return output
