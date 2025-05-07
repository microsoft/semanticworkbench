# Copyright (c) Microsoft. All rights reserved.

import json
import logging
from typing import Any

from mcp.server.fastmcp import Context
from mcp_extensions.llm.chat_completion import chat_completion
from mcp_extensions.llm.helpers import compile_messages
from mcp_extensions.llm.llm_types import ChatCompletionRequest, MessageT, UserMessage

from mcp_server_filesystem_edit import settings
from mcp_server_filesystem_edit.prompts.add_comments import (
    ADD_COMMENTS_CONVERT_MESSAGES,
    ADD_COMMENTS_MESSAGES,
    ADD_COMMENTS_TOOL_DEF,
    ADD_COMMENTS_TOOL_NAME,
)
from mcp_server_filesystem_edit.prompts.analyze_comments import COMMENT_ANALYSIS_MESSAGES, COMMENT_ANALYSIS_SCHEMA
from mcp_server_filesystem_edit.tools.edit_adapters.common import format_blocks_for_llm
from mcp_server_filesystem_edit.tools.edit_adapters.latex import blockify as latex_blockify
from mcp_server_filesystem_edit.tools.edit_adapters.latex import unblockify as latex_unblockify
from mcp_server_filesystem_edit.tools.edit_adapters.markdown import blockify as markdown_blockify
from mcp_server_filesystem_edit.tools.edit_adapters.markdown import unblockify as markdown_unblockify
from mcp_server_filesystem_edit.tools.helpers import format_chat_history
from mcp_server_filesystem_edit.types import Block, CommentOutput, CustomContext, FileOpRequest, FileOpTelemetry

logger = logging.getLogger(__name__)


class CommonComments:
    def __init__(self) -> None:
        self.telemetry = FileOpTelemetry()

    async def blockify(self, request: FileOpRequest) -> list[Block]:
        if request.file_type == "latex":
            blocks = latex_blockify(request.file_content)
        else:
            blocks = markdown_blockify(request.file_content)
        return blocks

    async def unblockify(self, request: FileOpRequest, blocks: list[Block]) -> str:
        if request.file_type == "latex":
            unblockified_doc = latex_unblockify(blocks)
        else:
            unblockified_doc = markdown_unblockify(blocks)
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
                "knowledge_cutoff": settings.knowledge_cutoff,
                "current_date": settings.current_date_func(),
                "context": context,
                "document": doc_for_llm,
                "chat_history": chat_history,
                "file_type": request.file_type,
            },
        )
        return comments_messages

    async def get_comments_reasoning(self, request: FileOpRequest, messages: list[MessageT]) -> str:
        mcp_messages = messages
        if request.request_type == "mcp" and isinstance(request.context, Context):
            mcp_messages = [messages[0]]  # Developer message
            mcp_messages.append(UserMessage(content=json.dumps({"variable": "history_messages"})))
            mcp_messages.append(messages[3])  # Document message

        reasoning_response = await chat_completion(
            request=ChatCompletionRequest(
                messages=mcp_messages,
                model=settings.comment_model,
                max_completion_tokens=15000,
                reasoning_effort="medium",
            ),
            provider=request.request_type,
            client=request.context if request.request_type == "mcp" else request.chat_completion_client,  # type: ignore
        )

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
            model=settings.convert_tool_calls_model,
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

    def format_comment(self, file_type: str, comment_text: str) -> str:
        """Returns a formatted comment based on file type."""
        if file_type == "markdown" or file_type == "word":
            return f"<!-- Feedback: {comment_text} -->\n"
        else:
            return f"% Feedback: {comment_text}\n"

    async def add_comments_to_content(self, request: FileOpRequest, parsed_comments: list[dict]) -> str:
        """
        Add comments to the document by inserting them at the start of identified blocks.
        """
        if not parsed_comments:
            return request.file_content

        blocks = await self.blockify(request)
        blocks_by_id = {block.id: block for block in blocks}

        for comment in parsed_comments:
            block_id = comment.get("block_id", 0)
            if block_id < 1:
                continue
            comment_text = comment.get("comment_text", "")
            if block_id in blocks_by_id:
                block = blocks_by_id[block_id]
                comment_line = self.format_comment(request.file_type, comment_text)
                block.content = comment_line + block.content

        updated_content = await self.unblockify(request, blocks)
        return updated_content

    async def construct_analyze_comments_prompt(
        self, request: FileOpRequest, document_with_new_comments: str
    ) -> list[MessageT]:
        """
        Constructs the prompt for analyzing comments.
        """
        chat_history = ""
        if request.request_type == "dev" and isinstance(request.context, CustomContext):
            chat_history = format_chat_history(request.context.chat_history)

        context = ""
        if request.request_type == "dev" and isinstance(request.context, CustomContext):
            context = request.context.additional_context

        comments_messages = compile_messages(
            messages=COMMENT_ANALYSIS_MESSAGES,
            variables={
                "knowledge_cutoff": settings.knowledge_cutoff,
                "current_date": settings.current_date_func(),
                "context": context,
                "document": document_with_new_comments,
                "chat_history": chat_history,
            },
        )
        return comments_messages

    async def get_analysis_response(self, request: FileOpRequest, messages: list[MessageT]) -> dict:
        mcp_messages = messages
        if request.request_type == "mcp" and isinstance(request.context, Context):
            mcp_messages = [messages[0]]  # Developer message
            mcp_messages.append(UserMessage(content=json.dumps({"variable": "history_messages"})))
            mcp_messages.append(messages[3])  # Document message

        analysis_response = await chat_completion(
            request=ChatCompletionRequest(
                messages=mcp_messages,
                model=settings.comment_analysis_model,
                max_completion_tokens=8000,
                temperature=0.5,
                structured_outputs=COMMENT_ANALYSIS_SCHEMA,
            ),
            provider=request.request_type,
            client=request.context if request.request_type == "mcp" else request.chat_completion_client,  # type: ignore
        )
        self.telemetry.change_summary_latency = analysis_response.response_duration
        comment_analysis = analysis_response.choices[0].json_message or {}
        logger.info(f"Comment analysis response:\n{comment_analysis}")
        return comment_analysis

    async def convert_to_instructions(self, json_message: dict) -> str:
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
                    edit_str = f'To address the comment "{comment_id}", please do the following:'
                    edit_instructions += f"{edit_str} {output_message}\n"
                elif not comment.get("is_actionable", False) and not comment.get("is_addressed", True):
                    assistant_str = f'To address the comment "{comment_id}",'
                    assistant_hints += f"{assistant_str} {output_message}\n"

        final_instructions = ""
        if edit_instructions or assistant_hints:
            final_instructions = f"{settings.feedback_tool_prefix}## Comments were added to the document, here are tips on how to address them\n\n"
            if assistant_hints:
                final_instructions += f"### Not immediately actionable (seek more information)\n{assistant_hints}\n"
            if edit_instructions:
                final_instructions += f"### Actionable comments (act on these by editing)\n{edit_instructions}\n"

        return final_instructions.strip()

    async def run(self, request: FileOpRequest, only_analyze: bool = False) -> CommentOutput:
        """
        Run the comment addition process for documents
        """
        self.telemetry.reset()
        if not only_analyze:
            # Add comments to the file
            blockified_doc = await self.blockify(request)
            comments_messages = await self.construct_comments_prompt(request, blockified_doc)
            reasoning = await self.get_comments_reasoning(request, comments_messages)
            logger.info(f"Comments reasoning:\n{reasoning}")
            convert_messages = await self.construct_convert_prompt(reasoning)
            convert_response, parsed_comments = await self.get_convert_response(request, convert_messages)
            new_content = await self.add_comments_to_content(request, parsed_comments)

            # Analyze the comments
            analyze_comments_messages = await self.construct_analyze_comments_prompt(request, new_content)
            comment_analysis = await self.get_analysis_response(request, analyze_comments_messages)
            comment_instructions = await self.convert_to_instructions(comment_analysis)

            output = CommentOutput(
                new_content=new_content,
                comment_instructions=comment_instructions,
                reasoning=reasoning,
                tool_calls=convert_response.choices[0].message.tool_calls or [],
                llm_latency=self.telemetry.reasoning_latency
                + self.telemetry.convert_latency
                + self.telemetry.change_summary_latency,
            )
            return output
        else:
            # Analyze the comments
            analyze_comments_messages = await self.construct_analyze_comments_prompt(request, request.file_content)
            comment_analysis = await self.get_analysis_response(request, analyze_comments_messages)
            comment_instructions = await self.convert_to_instructions(comment_analysis)
            output = CommentOutput(
                new_content=request.file_content,
                comment_instructions=comment_instructions,
                reasoning="",
                tool_calls=[],
                llm_latency=self.telemetry.change_summary_latency,
            )
            return output
