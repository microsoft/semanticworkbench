# Copyright (c) Microsoft. All rights reserved.

import json
import logging

import pendulum
from mcp.server.fastmcp import Context
from mcp_extensions.llm.chat_completion import chat_completion
from mcp_extensions.llm.helpers import compile_messages
from mcp_extensions.llm.llm_types import ChatCompletionRequest, ChatCompletionResponse, MessageT, UserMessage

from mcp_server_filesystem_edit import settings
from mcp_server_filesystem_edit.prompts.latex_edit import LATEX_EDIT_REASONING_MESSAGES
from mcp_server_filesystem_edit.prompts.markdown_edit import (
    MD_EDIT_CHANGES_MESSAGES,
    MD_EDIT_CONVERT_MESSAGES,
    MD_EDIT_REASONING_MESSAGES,
    MD_EDIT_TOOL_DEF,
    MD_EDIT_TOOL_NAME,
    SEND_MESSAGE_TOOL_DEF,
    SEND_MESSAGE_TOOL_NAME,
)
from mcp_server_filesystem_edit.tools.edit_adapters.common import execute_tools, format_blocks_for_llm
from mcp_server_filesystem_edit.tools.edit_adapters.latex import blockify as latex_blockify
from mcp_server_filesystem_edit.tools.edit_adapters.latex import unblockify as latex_unblockify
from mcp_server_filesystem_edit.tools.edit_adapters.markdown import blockify as markdown_blockify
from mcp_server_filesystem_edit.tools.edit_adapters.markdown import unblockify as markdown_unblockify
from mcp_server_filesystem_edit.tools.helpers import format_chat_history
from mcp_server_filesystem_edit.types import Block, CustomContext, EditOutput, EditTelemetry, FileOpRequest

logger = logging.getLogger(__name__)


class CommonEdit:
    def __init__(self) -> None:
        self.telemetry = EditTelemetry()

    async def blockify(self, request: FileOpRequest) -> list[Block]:
        if request.file_type == "latex":
            blocks = latex_blockify(request.file_content)
        elif request.file_type == "markdown":
            blocks = markdown_blockify(request.file_content)
        else:
            raise ValueError(f"Unsupported file type: {request.file_type}")
        return blocks

    async def unblockify(self, request: FileOpRequest, blocks: list[Block]) -> str:
        if request.file_type == "latex":
            unblockified_doc = latex_unblockify(blocks)
        else:
            unblockified_doc = markdown_unblockify(blocks)
        return unblockified_doc

    async def construct_reasoning_prompt(self, request: FileOpRequest, blockified_doc: list[Block]) -> list[MessageT]:
        doc_for_llm = await format_blocks_for_llm(blockified_doc)

        chat_history = ""
        if request.request_type == "dev" and isinstance(request.context, CustomContext):
            chat_history = format_chat_history(request.context.chat_history)

        context = ""
        if request.request_type == "dev" and isinstance(request.context, CustomContext):
            context = request.context.additional_context

        reasoning_messages = compile_messages(
            messages=LATEX_EDIT_REASONING_MESSAGES if request.file_type == "latex" else MD_EDIT_REASONING_MESSAGES,
            variables={
                "knowledge_cutoff": "2023-10",
                "current_date": pendulum.now().format("YYYY-MM-DD"),
                "task": request.task,
                "context": context,
                "document": doc_for_llm,
                "chat_history": chat_history,
            },
        )
        return reasoning_messages

    async def get_reasoning_response(self, request: FileOpRequest, messages: list[MessageT]) -> str:
        if request.request_type == "mcp" and isinstance(request.context, Context):
            mcp_messages = [messages[0]]  # Developer message
            mcp_messages.append(UserMessage(content=json.dumps({"variable": "attachment_messages"})))
            mcp_messages.append(UserMessage(content=json.dumps({"variable": "history_messages"})))
            mcp_messages.append(messages[3])  # Document message
            reasoning_response = await chat_completion(
                request=ChatCompletionRequest(
                    messages=mcp_messages,
                    model="o3-mini",
                    max_completion_tokens=20000,
                    reasoning_effort="high",
                ),
                provider="mcp",
                client=request.context,
            )
        elif request.request_type == "dev":
            reasoning_response = await chat_completion(
                request=ChatCompletionRequest(
                    messages=messages,
                    model="o3-mini",
                    max_completion_tokens=20000,
                    reasoning_effort="high",
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
            messages=MD_EDIT_CONVERT_MESSAGES,
            variables={"reasoning": reasoning},
        )
        return convert_messages

    async def get_convert_response(self, request: FileOpRequest, messages: list[MessageT]) -> ChatCompletionResponse:
        chat_completion_request = ChatCompletionRequest(
            messages=messages,
            model="gpt-4o",
            temperature=0,
            max_completion_tokens=8000,
            tools=[MD_EDIT_TOOL_DEF, SEND_MESSAGE_TOOL_DEF],
            tool_choice="required",
            parallel_tool_calls=False,
        )
        convert_response = await chat_completion(
            request=chat_completion_request,
            provider=request.request_type,
            client=request.context if request.request_type == "mcp" else request.chat_completion_client,  # type: ignore
        )
        self.telemetry.convert_latency = convert_response.response_duration
        return convert_response

    async def execute_tool_calls(
        self, request: FileOpRequest, convert_response: ChatCompletionResponse
    ) -> tuple[str, str]:
        updated_doc_markdown = request.file_content
        output_message = ""
        if convert_response.choices[0].message.tool_calls:
            tool_call = convert_response.choices[0].message.tool_calls[0].function
            logger.info(f"Tool call:\n{tool_call}")
            # If the the model called the send_message, don't update the doc and return the message
            if tool_call.name == SEND_MESSAGE_TOOL_NAME:
                output_message = settings.doc_editor_prefix + convert_response.choices[0].message.content
            elif tool_call.name == MD_EDIT_TOOL_NAME:
                tool_args = tool_call.arguments
                blocks = await self.blockify(request)
                blocks = execute_tools(blocks=blocks, edit_tool_call={"name": tool_call.name, "arguments": tool_args})
                updated_doc_markdown = await self.unblockify(request, blocks)
        else:
            output_message = (
                settings.doc_editor_prefix + "Something went wrong when editing the document and no changes were made."
            )

        return updated_doc_markdown, output_message

    async def run_change_summary(self, before_doc: str, after_doc: str, edit_request: FileOpRequest) -> str:
        change_summary_messages = compile_messages(
            messages=MD_EDIT_CHANGES_MESSAGES,
            variables={
                "before_doc": before_doc,
                "after_doc": after_doc,
            },
        )
        change_summary_response = await chat_completion(
            request=ChatCompletionRequest(
                messages=change_summary_messages,
                model="gpt-4o",
                max_completion_tokens=1000,
            ),
            provider=edit_request.request_type,
            client=edit_request.context if edit_request.request_type == "mcp" else edit_request.chat_completion_client,  # type: ignore
        )
        self.telemetry.change_summary_latency = change_summary_response.response_duration

        change_summary = change_summary_response.choices[0].message.content
        change_summary = settings.doc_editor_prefix + change_summary
        return change_summary

    async def run(self, request: FileOpRequest) -> EditOutput:
        """
        Run the edit request and return the result.
        """
        self.telemetry.reset()
        blockified_doc = await self.blockify(request)
        reasoning_messages = await self.construct_reasoning_prompt(request, blockified_doc)
        reasoning = await self.get_reasoning_response(request, reasoning_messages)
        logger.info(f"Reasoning:\n{reasoning}")
        convert_messages = await self.construct_convert_prompt(reasoning)
        convert_response = await self.get_convert_response(request, convert_messages)
        updated_doc_markdown, output_message = await self.execute_tool_calls(request, convert_response)
        change_summary = await self.run_change_summary(
            before_doc=request.file_content,
            after_doc=updated_doc_markdown,
            edit_request=request,
        )

        output = EditOutput(
            change_summary=change_summary,
            output_message=output_message,
            new_content=updated_doc_markdown,
            reasoning=reasoning,
            tool_calls=convert_response.choices[0].message.tool_calls or [],
            llm_latency=self.telemetry.reasoning_latency
            + self.telemetry.convert_latency
            + self.telemetry.change_summary_latency,
        )
        return output
