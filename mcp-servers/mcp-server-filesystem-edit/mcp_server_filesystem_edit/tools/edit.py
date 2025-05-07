# Copyright (c) Microsoft. All rights reserved.

import json
import logging
import re

from mcp.server.fastmcp import Context
from mcp_extensions.llm.chat_completion import chat_completion
from mcp_extensions.llm.helpers import compile_messages
from mcp_extensions.llm.llm_types import ChatCompletionRequest, ChatCompletionResponse, MessageT, UserMessage

from mcp_server_filesystem_edit import settings
from mcp_server_filesystem_edit.prompts.latex_edit import LATEX_EDIT_REASONING_MESSAGES
from mcp_server_filesystem_edit.prompts.markdown_draft import MD_DRAFT_REASONING_MESSAGES
from mcp_server_filesystem_edit.prompts.markdown_edit import (
    MARKDOWN_EDIT_FORMAT_INSTRUCTIONS,
    MD_EDIT_CHANGES_MESSAGES,
    MD_EDIT_CONVERT_MESSAGES,
    MD_EDIT_REASONING_MESSAGES,
    MD_EDIT_TOOL_DEF,
    MD_EDIT_TOOL_NAME,
    SEND_MESSAGE_TOOL_DEF,
    SEND_MESSAGE_TOOL_NAME,
    WORD_EDIT_FORMAT_INSTRUCTIONS,
)
from mcp_server_filesystem_edit.prompts.powerpoint_edit import PPT_EDIT_REASONING_MESSAGES, PPT_EDIT_TOOL_DEF
from mcp_server_filesystem_edit.tools.edit_adapters.common import execute_tools, format_blocks_for_llm
from mcp_server_filesystem_edit.tools.edit_adapters.latex import blockify as latex_blockify
from mcp_server_filesystem_edit.tools.edit_adapters.latex import unblockify as latex_unblockify
from mcp_server_filesystem_edit.tools.edit_adapters.markdown import blockify as markdown_blockify
from mcp_server_filesystem_edit.tools.edit_adapters.markdown import unblockify as markdown_unblockify
from mcp_server_filesystem_edit.tools.helpers import TokenizerOpenAI, format_chat_history
from mcp_server_filesystem_edit.types import Block, CustomContext, EditOutput, FileOpRequest, FileOpTelemetry

logger = logging.getLogger(__name__)

# region CommonEdit


class CommonEdit:
    def __init__(self) -> None:
        self.telemetry = FileOpTelemetry()
        self.tokenizer = TokenizerOpenAI(model="gpt-4o")

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

    async def take_draft_path(self, request: FileOpRequest) -> bool:
        """
        Decides if we should take a separate path that will simply use a single prompt
        that rewrites the document in a single step rather than using editing logic.

        Returns True if we should take the draft path, False otherwise.
        """
        if request.file_type == "latex":
            return False
        else:
            # If the document is over the rewrite threshold tokens, we do not take the draft path.
            num_tokens = self.tokenizer.num_tokens_in_str(request.file_content)
            if num_tokens > settings.rewrite_threshold:
                return False
        return True

    async def get_draft_response(self, request: FileOpRequest) -> str:
        """
        Get the rewritten document
        """
        chat_history = ""
        if request.request_type == "dev" and isinstance(request.context, CustomContext):
            chat_history = format_chat_history(request.context.chat_history)
        context = ""
        if request.request_type == "dev" and isinstance(request.context, CustomContext):
            context = request.context.additional_context
        messages = compile_messages(
            messages=MD_DRAFT_REASONING_MESSAGES,
            variables={
                "knowledge_cutoff": settings.knowledge_cutoff,
                "current_date": settings.current_date_func(),
                "task": request.task,
                "context": context,
                "document": request.file_content,
                "chat_history": chat_history,
                "format_instructions": (
                    WORD_EDIT_FORMAT_INSTRUCTIONS if request.file_type == "word" else MARKDOWN_EDIT_FORMAT_INSTRUCTIONS
                ),
            },
        )
        mcp_messages = messages
        if request.request_type == "mcp" and isinstance(request.context, Context):
            mcp_messages = [messages[0]]  # Developer message
            mcp_messages.append(UserMessage(content=json.dumps({"variable": "history_messages"})))
            mcp_messages.append(messages[3])  # Document message

        reasoning_response = await chat_completion(
            request=ChatCompletionRequest(
                messages=mcp_messages,
                model=settings.draft_path_model,
                max_completion_tokens=20000,
                temperature=1,
            ),
            provider=request.request_type,
            client=request.context if request.request_type == "mcp" else request.chat_completion_client,  # type: ignore
        )
        self.telemetry.reasoning_latency = reasoning_response.response_duration
        draft = reasoning_response.choices[0].message.content
        # Look for content between <new_document> tags, otherwise return the entire response as the doc.
        pattern = r"<new_document>(.*?)</new_document>"
        match = re.search(pattern, draft, re.DOTALL)
        if match:
            draft = match.group(1).strip()
        return draft

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
                "knowledge_cutoff": settings.knowledge_cutoff,
                "current_date": settings.current_date_func(),
                "task": request.task,
                "context": context,
                "document": doc_for_llm,
                "chat_history": chat_history,
                "format_instructions": (
                    WORD_EDIT_FORMAT_INSTRUCTIONS if request.file_type == "word" else MARKDOWN_EDIT_FORMAT_INSTRUCTIONS
                ),
            },
        )
        return reasoning_messages

    async def get_reasoning_response(self, request: FileOpRequest, messages: list[MessageT]) -> str:
        mcp_messages = messages
        if request.request_type == "mcp" and isinstance(request.context, Context):
            mcp_messages = [messages[0]]  # Developer message
            mcp_messages.append(UserMessage(content=json.dumps({"variable": "history_messages"})))
            mcp_messages.append(messages[3])  # Document message
        reasoning_response = await chat_completion(
            request=ChatCompletionRequest(
                messages=mcp_messages,
                model=settings.edit_model,
                max_completion_tokens=20000,
                reasoning_effort="high",
            ),
            provider=request.request_type,
            client=request.context if request.request_type == "mcp" else request.chat_completion_client,  # type: ignore
        )
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
            model=settings.convert_tool_calls_model,
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
                model=settings.summarization_model,
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

        if await self.take_draft_path(request):
            logger.info("Taking draft path instead of editing.")
            updated_doc_markdown = await self.get_draft_response(request)
            output_message = ""
            reasoning = ""
            tool_calls = []
        else:
            blockified_doc = await self.blockify(request)
            reasoning_messages = await self.construct_reasoning_prompt(request, blockified_doc)
            reasoning = await self.get_reasoning_response(request, reasoning_messages)
            logger.info(f"Reasoning:\n{reasoning}")
            convert_messages = await self.construct_convert_prompt(reasoning)
            convert_response = await self.get_convert_response(request, convert_messages)
            tool_calls = convert_response.choices[0].message.tool_calls or []
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
            tool_calls=tool_calls,
            llm_latency=self.telemetry.reasoning_latency
            + self.telemetry.convert_latency
            + self.telemetry.change_summary_latency,
        )
        return output


# endregion

# region PowerpointEdit


class PowerpointEdit:
    def __init__(self) -> None:
        self.telemetry = FileOpTelemetry()

    async def blockify(self, request: FileOpRequest) -> list[Block]:
        blocks = []

        slide_pattern = r'<slide\s+index=(?:"?(\d+)"?).*?</slide>'

        slide_matches = re.finditer(slide_pattern, request.file_content, re.DOTALL)
        for match in slide_matches:
            slide_content = match.group(0)
            slide_index = match.group(1)

            try:
                slide_index = int(slide_index)
            except ValueError:
                logger.error(f"Invalid slide number: {slide_index}")
                continue

            block = Block(
                id=slide_index,
                content=slide_content,
            )
            blocks.append(block)
        return blocks

    async def unblockify(self, blocks: list[Block]) -> str:
        return "".join(block.content for block in blocks)

    async def construct_reasoning_prompt(self, request: FileOpRequest, blockified_doc: list[Block]) -> list[MessageT]:
        doc_for_llm = await format_blocks_for_llm(blockified_doc)

        chat_history = ""
        if request.request_type == "dev" and isinstance(request.context, CustomContext):
            chat_history = format_chat_history(request.context.chat_history)

        context = ""
        if request.request_type == "dev" and isinstance(request.context, CustomContext):
            context = request.context.additional_context

        reasoning_messages = compile_messages(
            messages=PPT_EDIT_REASONING_MESSAGES,
            variables={
                "knowledge_cutoff": settings.knowledge_cutoff,
                "current_date": settings.current_date_func(),
                "task": request.task,
                "context": context,
                "document": doc_for_llm,
                "chat_history": chat_history,
            },
        )
        return reasoning_messages

    async def get_reasoning_response(self, request: FileOpRequest, messages: list[MessageT]) -> str:
        mcp_messages = messages
        if request.request_type == "mcp" and isinstance(request.context, Context):
            mcp_messages = [messages[0]]  # Developer message
            mcp_messages.append(UserMessage(content=json.dumps({"variable": "history_messages"})))
            mcp_messages.append(messages[3])  # Document message
        reasoning_response = await chat_completion(
            request=ChatCompletionRequest(
                messages=mcp_messages,
                model=settings.edit_model,
                max_completion_tokens=20000,
                reasoning_effort="high",
            ),
            provider=request.request_type,
            client=request.context if request.request_type == "mcp" else request.chat_completion_client,  # type: ignore
        )
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
            model=settings.convert_tool_calls_model,
            temperature=0,
            max_completion_tokens=8000,
            tools=[PPT_EDIT_TOOL_DEF, SEND_MESSAGE_TOOL_DEF],
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
                updated_doc_markdown = await self.unblockify(blocks)
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
                model=settings.summarization_model,
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
        self.telemetry.reset()
        blockified_doc = await self.blockify(request)
        reasoning_messages = await self.construct_reasoning_prompt(request, blockified_doc)
        reasoning = await self.get_reasoning_response(request, reasoning_messages)
        logger.info(f"Reasoning:\n{reasoning}")
        convert_messages = await self.construct_convert_prompt(reasoning)
        convert_response = await self.get_convert_response(request, convert_messages)
        tool_calls = convert_response.choices[0].message.tool_calls or []
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
            tool_calls=tool_calls,
            llm_latency=self.telemetry.reasoning_latency
            + self.telemetry.convert_latency
            + self.telemetry.change_summary_latency,
        )
        return output


# endregion
