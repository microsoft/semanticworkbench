import json
import logging
from typing import Any

import pendulum
from mcp.server.fastmcp import Context
from mcp_extensions.llm.chat_completion import chat_completion
from mcp_extensions.llm.helpers import compile_messages
from mcp_extensions.llm.llm_types import ChatCompletionRequest, MessageT, UserMessage

from mcp_server_filesystem_edit.prompts.add_comments import (
    ADD_COMMENTS_CONVERT_MESSAGES,
    ADD_COMMENTS_MESSAGES,
    ADD_COMMENTS_TOOL_DEF,
    ADD_COMMENTS_TOOL_NAME,
)
from mcp_server_filesystem_edit.tools.edit_adapters.common import format_blocks_for_llm
from mcp_server_filesystem_edit.tools.edit_adapters.latex import blockify as latex_blockify
from mcp_server_filesystem_edit.tools.edit_adapters.latex import unblockify as latex_unblockify
from mcp_server_filesystem_edit.tools.helpers import format_chat_history
from mcp_server_filesystem_edit.types import Block, CommentOutput, CustomContext, EditTelemetry, FileOpRequest

logger = logging.getLogger(__name__)


class CommonComments:
    def __init__(self) -> None:
        self.telemetry = EditTelemetry()

    async def blockify(self, request: FileOpRequest) -> list[Block]:
        if request.file_type == "latex":
            blocks = latex_blockify(request.file_content)
        else:
            raise ValueError(f"Unsupported file type for comments: {request.file_type}")
        return blocks

    async def unblockify(self, request: FileOpRequest, blocks: list[Block]) -> str:
        if request.file_type == "latex":
            unblockified_doc = latex_unblockify(blocks)
        else:
            raise ValueError(f"Unsupported file type for comments: {request.file_type}")
        return unblockified_doc

    async def construct_comments_prompt(self, request: FileOpRequest, blockified_doc: list[Block]) -> list[MessageT]:
        doc_for_llm = await format_blocks_for_llm(blockified_doc)

        chat_history = ""
        if request.request_type == "dev" and isinstance(request.context, CustomContext):
            chat_history = format_chat_history(request.context.chat_history)

        context = ""
        if request.request_type == "dev" and isinstance(request.context, CustomContext):
            context = request.context.additional_context

        comments_messages = compile_messages(
            messages=ADD_COMMENTS_MESSAGES,
            variables={
                "knowledge_cutoff": "2023-10",
                "current_date": pendulum.now().format("YYYY-MM-DD"),
                "context": context,
                "document": doc_for_llm,
                "chat_history": chat_history,
            },
        )
        return comments_messages

    async def get_comments_reasoning(self, request: FileOpRequest, messages: list[MessageT]) -> str:
        if request.request_type == "mcp" and isinstance(request.context, Context):
            mcp_messages = [messages[0]]  # Developer message
            mcp_messages.append(UserMessage(content=json.dumps({"variable": "attachment_messages"})))
            mcp_messages.append(UserMessage(content=json.dumps({"variable": "history_messages"})))
            mcp_messages.append(messages[3])  # Document message
            reasoning_response = await chat_completion(
                request=ChatCompletionRequest(
                    messages=mcp_messages,
                    model="o3-mini",
                    max_completion_tokens=15000,
                    reasoning_effort="medium",
                ),
                provider="mcp",
                client=request.context,
            )
        elif request.request_type == "dev":
            reasoning_response = await chat_completion(
                request=ChatCompletionRequest(
                    messages=messages,
                    model="o3-mini",
                    max_completion_tokens=15000,
                    reasoning_effort="medium",
                ),
                provider="azure_openai",
                client=request.chat_completion_client,  # type: ignore
            )
        else:
            raise ValueError(f"Invalid request type: {request.request_type}")

        self.telemetry.reasoning_latency = reasoning_response.response_duration
        reasoning = reasoning_response.choices[0].message.content
        return reasoning

    async def construct_convert_prompt(self, reasoning: str) -> list[MessageT]:
        convert_messages = compile_messages(
            messages=ADD_COMMENTS_CONVERT_MESSAGES,
            variables={"reasoning": reasoning},
        )
        return convert_messages

    async def get_convert_response(self, request: FileOpRequest, messages: list[MessageT]) -> tuple[Any, list[dict]]:
        chat_completion_request = ChatCompletionRequest(
            messages=messages,
            model="gpt-4o",
            temperature=0,
            max_completion_tokens=8000,
            tools=[ADD_COMMENTS_TOOL_DEF],
            tool_choice="required",
            parallel_tool_calls=False,
        )
        convert_response = await chat_completion(
            request=chat_completion_request,
            provider=request.request_type,
            client=request.context if request.request_type == "mcp" else request.chat_completion_client,  # type: ignore
        )
        self.telemetry.convert_latency = convert_response.response_duration

        # Extract comments from the tool call
        parsed_comments = []
        if (
            convert_response.choices[0].message.tool_calls
            and convert_response.choices[0].message.tool_calls[0].function.name == ADD_COMMENTS_TOOL_NAME
        ):
            tool_call = convert_response.choices[0].message.tool_calls[0].function
            parsed_comments = tool_call.arguments.get("comments", [])
            logger.info(f"Extracted {len(parsed_comments)} comments from tool call")

        return convert_response, parsed_comments

    async def add_comments_to_content(self, request: FileOpRequest, parsed_comments: list[dict]) -> str:
        """Add comments to the LaTeX document by inserting them at the start of identified blocks."""
        if not parsed_comments:
            return request.file_content

        blocks = await self.blockify(request)
        blocks_by_id = {block.id: block for block in blocks}

        for comment in parsed_comments:
            block_id = comment.get("block_id", 0)
            comment_text = comment.get("comment_text", "")

            if block_id in blocks_by_id:
                block = blocks_by_id[block_id]
                comment_line = f"% Feedback: {comment_text}\n"
                block.content = comment_line + block.content

        updated_content = await self.unblockify(request, blocks)
        return updated_content

    async def summarize_comments(self, comments: list[dict]) -> str:
        if not comments:
            return "No comments were added to the document."

        summary_parts = ["I've added the following comments to your LaTeX document:"]

        for _, comment in enumerate(comments, 1):
            comment_text = comment.get("comment_text", "")
            summary_parts.append(f"   **Comment**: {comment_text}")
            summary_parts.append("")

        return "\n".join(summary_parts)

    async def run(self, request: FileOpRequest) -> CommentOutput:
        """Run the comment addition process for LaTeX documents and return the result."""
        if request.file_type != "latex":
            raise ValueError(f"File type '{request.file_type}' is not supported for this operation. Expected 'latex'.")

        self.telemetry.reset()
        blockified_doc = await self.blockify(request)
        comments_messages = await self.construct_comments_prompt(request, blockified_doc)
        reasoning = await self.get_comments_reasoning(request, comments_messages)
        logger.info(f"Comments reasoning:\n{reasoning}")

        convert_messages = await self.construct_convert_prompt(reasoning)
        convert_response, parsed_comments = await self.get_convert_response(request, convert_messages)

        new_content = await self.add_comments_to_content(request, parsed_comments)
        comment_summary = await self.summarize_comments(parsed_comments)

        output = CommentOutput(
            new_content=new_content,
            comment_summary=comment_summary,
            reasoning=reasoning,
            tool_calls=convert_response.choices[0].message.tool_calls or [],
            llm_latency=self.telemetry.reasoning_latency + self.telemetry.convert_latency,
        )
        return output
