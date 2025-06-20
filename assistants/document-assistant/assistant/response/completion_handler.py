import json
import logging
import re
import time
from typing import List

import deepmerge
from assistant_extensions.mcp import (
    ExtendedCallToolRequestParams,
    MCPSession,
    OpenAISamplingHandler,
    handle_mcp_tool_call,
)
from openai.types.chat import (
    ChatCompletion,
    ChatCompletionToolMessageParam,
    ParsedChatCompletion,
)
from openai_client import OpenAIRequestConfig, num_tokens_from_messages
from semantic_workbench_api_model.workbench_model import (
    MessageType,
    NewConversationMessage,
)
from semantic_workbench_assistant.assistant_app import (
    ConversationContext,
)

from assistant.context_management.conv_compaction import get_compaction_data
from assistant.filesystem import AttachmentsExtension
from assistant.filesystem._tasks import get_filesystem_metadata
from assistant.guidance.dynamic_ui_inspector import update_dynamic_ui_state
from assistant.guidance.guidance_prompts import DYNAMIC_UI_TOOL_NAME, DYNAMIC_UI_TOOL_RESULT

from .models import StepResult
from .utils import (
    extract_content_from_mcp_tool_calls,
    get_response_duration_message,
    get_token_usage_message,
)

logger = logging.getLogger(__name__)


async def handle_completion(
    sampling_handler: OpenAISamplingHandler,
    step_result: StepResult,
    completion: ParsedChatCompletion | ChatCompletion,
    mcp_sessions: List[MCPSession],
    context: ConversationContext,
    request_config: OpenAIRequestConfig,
    silence_token: str,
    metadata_key: str,
    response_start_time: float,
    attachments_extension: AttachmentsExtension,
    guidance_enabled: bool,
) -> StepResult:
    # get service and request configuration for generative model
    request_config = request_config

    # get the total tokens used for the completion
    total_tokens = completion.usage.total_tokens if completion.usage else 0

    content: str | None = None

    if (completion.choices[0].message.content is not None) and (completion.choices[0].message.content.strip() != ""):
        content = completion.choices[0].message.content

    # check if the completion has tool calls
    tool_calls: list[ExtendedCallToolRequestParams] = []
    if completion.choices[0].message.tool_calls:
        ai_context, tool_calls = extract_content_from_mcp_tool_calls([
            ExtendedCallToolRequestParams(
                id=tool_call.id,
                name=tool_call.function.name,
                arguments=json.loads(
                    tool_call.function.arguments,
                ),
            )
            for tool_call in completion.choices[0].message.tool_calls
        ])
        if content is None:
            if ai_context is not None and ai_context.strip() != "":
                content = ai_context

    if content is None:
        content = ""

    # update the metadata with debug information
    deepmerge.always_merger.merge(
        step_result.metadata,
        {
            "debug": {
                metadata_key: {
                    "response": completion.model_dump() if completion else "[no response from openai]",
                },
            },
        },
    )

    # Add tool calls to the metadata
    deepmerge.always_merger.merge(
        step_result.metadata,
        {
            "tool_calls": [tool_call.model_dump(mode="json") for tool_call in tool_calls],
        },
    )

    # Create the footer items for the response
    footer_items = []

    # Add the token usage message to the footer items
    if total_tokens > 0:
        completion_tokens = completion.usage.completion_tokens if completion.usage else 0
        request_tokens = total_tokens - completion_tokens
        footer_items.append(
            get_token_usage_message(
                max_tokens=request_config.max_tokens,
                total_tokens=total_tokens,
                request_tokens=request_tokens,
                completion_tokens=completion_tokens,
            )
        )

        await context.update_conversation(
            metadata={
                "token_counts": {
                    "total": total_tokens,
                    "max": request_config.max_tokens,
                }
            }
        )

    # Track the end time of the response generation and calculate duration
    response_end_time = time.time()
    response_duration = response_end_time - response_start_time

    # Add the response duration to the footer items
    footer_items.append(get_response_duration_message(response_duration))

    # Update the metadata with the footer items
    deepmerge.always_merger.merge(
        step_result.metadata,
        {
            "footer_items": footer_items,
        },
    )

    # Set the conversation tokens for the turn result
    step_result.conversation_tokens = total_tokens

    # strip out the username from the response
    if content.startswith("["):
        content = re.sub(r"\[.*\]:\s", "", content)

    await context.send_messages(
        NewConversationMessage(
            content=content,
            message_type=MessageType.chat,
            metadata=step_result.metadata,
        )
    )

    # region Tool Logic

    # Check for tool calls
    if len(tool_calls) == 0:
        # No tool calls, exit the loop
        step_result.status = "final"
    # Handle DYNAMIC_UI_TOOL_NAME in a special way
    elif guidance_enabled and tool_calls[0].name == DYNAMIC_UI_TOOL_NAME:
        await update_dynamic_ui_state(context, tool_calls[0].arguments)

        # If this tool is called, we assume its the only tool
        step_result.conversation_tokens += num_tokens_from_messages(
            messages=[
                ChatCompletionToolMessageParam(
                    role="tool",
                    content=DYNAMIC_UI_TOOL_RESULT,
                    tool_call_id=tool_calls[0].id,
                )
            ],
            model=request_config.model,
        )
        deepmerge.always_merger.merge(
            step_result.metadata,
            {
                "tool_result": {
                    "content": DYNAMIC_UI_TOOL_RESULT,
                    "tool_call_id": tool_calls[0].id,
                },
            },
        )
        await context.send_messages(
            NewConversationMessage(
                content=DYNAMIC_UI_TOOL_RESULT,
                message_type=MessageType.note,
                metadata=step_result.metadata,
            )
        )

    # Handle the view tool call
    elif tool_calls[0].name == "view":
        path = (tool_calls[0].arguments or {}).get("path", "")
        # First try to find the path as an editable file
        file_content = await attachments_extension._inspectors.get_file_content(context, path)

        # Then try to find the path as an attachment file
        if file_content is None:
            file_content = await attachments_extension.get_attachment(context, path)

        # Finally try to find the path as a conversation file.
        if file_content is None:
            compaction_data = await get_compaction_data(context)
            for chunk in compaction_data.compaction_data.values():
                if chunk.chunk_name == path:
                    file_content = chunk.original_conversation_text
                    break

        if file_content is None:
            file_content = f"File at path {path} not found. Please pay attention to the available files and try again."
        else:
            file_content = f"<file path={path}>{file_content}</file>"

        step_result.conversation_tokens += num_tokens_from_messages(
            messages=[
                ChatCompletionToolMessageParam(
                    role="tool",
                    content=file_content,
                    tool_call_id=tool_calls[0].id,
                )
            ],
            model=request_config.model,
        )
        deepmerge.always_merger.merge(
            step_result.metadata,
            {
                "tool_result": {
                    "content": file_content,
                    "tool_call_id": tool_calls[0].id,
                },
            },
        )
        await context.send_messages(
            NewConversationMessage(
                content=file_content,
                message_type=MessageType.note,
                metadata=step_result.metadata,
            )
        )
    elif tool_calls[0].name == "ls":
        # Need to get all the available files and present it to the model.
        attachment_filenames = await attachments_extension.get_attachment_filenames(context)
        doc_editor_filenames = await attachments_extension._inspectors.list_document_filenames(context)
        compaction_data = await get_compaction_data(context)
        filesystem_metadata = await get_filesystem_metadata(context)

        # Tuple of (filename, permission, summary)
        all_files = [(filename, "-r--", filesystem_metadata.get(filename, "")) for filename in attachment_filenames]
        all_files.extend([
            (filename, "-rw-", filesystem_metadata.get(filename, "")) for filename in doc_editor_filenames
        ])
        for chunk in compaction_data.compaction_data.values():
            all_files.append((chunk.chunk_name, "-r--", chunk.compacted_text))

        all_files.sort(key=lambda x: x[0].lower())

        # Format the file list into a string
        ls_string = ""
        for _, (filename, permission, summary) in enumerate(all_files):
            ls_string += f"{filename} ({permission}) - {summary}\n"

        if ls_string == "":
            ls_string = "No files currently available in the filesystem."

        step_result.conversation_tokens += num_tokens_from_messages(
            messages=[
                ChatCompletionToolMessageParam(
                    role="tool",
                    content=ls_string,
                    tool_call_id=tool_calls[0].id,
                )
            ],
            model=request_config.model,
        )
        deepmerge.always_merger.merge(
            step_result.metadata,
            {
                "tool_result": {
                    "content": ls_string,
                    "tool_call_id": tool_calls[0].id,
                },
            },
        )
        await context.send_messages(
            NewConversationMessage(
                content=ls_string,
                message_type=MessageType.note,
                metadata=step_result.metadata,
            )
        )
    else:
        # Handle MCP tool calls
        tool_call_count = 0
        for tool_call in tool_calls:
            tool_call_count += 1
            tool_call_status = f"using tool `{tool_call.name}`"
            async with context.set_status(f"{tool_call_status}..."):
                try:
                    tool_call_result = await handle_mcp_tool_call(
                        mcp_sessions,
                        tool_call,
                        f"{metadata_key}:request:tool_call_{tool_call_count}",
                    )
                except Exception as e:
                    logger.exception(f"Error handling tool call '{tool_call.name}': {e}")
                    deepmerge.always_merger.merge(
                        step_result.metadata,
                        {
                            "debug": {
                                f"{metadata_key}:request:tool_call_{tool_call_count}": {
                                    "error": str(e),
                                },
                            },
                        },
                    )
                    await context.send_messages(
                        NewConversationMessage(
                            content=f"Error executing tool '{tool_call.name}': {e}",
                            message_type=MessageType.notice,
                            metadata=step_result.metadata,
                        )
                    )
                    step_result.status = "error"
                    return step_result

            # Update content and metadata with tool call result metadata
            deepmerge.always_merger.merge(step_result.metadata, tool_call_result.metadata)

            # FIXME only supporting 1 content item and it's text for now, should support other content types/quantity
            # Get the content from the tool call result
            content = next(
                (content_item.text for content_item in tool_call_result.content if content_item.type == "text"),
                "[tool call returned no content]",
            )

            # Add the token count for the tool call result to the total token count
            step_result.conversation_tokens += num_tokens_from_messages(
                messages=[
                    ChatCompletionToolMessageParam(
                        role="tool",
                        content=content,
                        tool_call_id=tool_call.id,
                    )
                ],
                model=request_config.model,
            )

            # Add the tool_result payload to metadata
            deepmerge.always_merger.merge(
                step_result.metadata,
                {
                    "tool_result": {
                        "content": content,
                        "tool_call_id": tool_call.id,
                    },
                },
            )

            await context.send_messages(
                NewConversationMessage(
                    content=content,
                    message_type=MessageType.note,
                    metadata=step_result.metadata,
                )
            )

    # endregion

    return step_result
