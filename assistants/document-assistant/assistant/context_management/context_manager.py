import logging

from openai.types.chat import (
    ChatCompletionMessageParam,
    ChatCompletionToolParam,
)
from semantic_workbench_assistant.assistant_app import (
    ConversationContext,
)

from assistant.config import AssistantConfigModel
from assistant.context_management.conv_compaction import get_compaction_data
from assistant.context_management.inspector import ContextManagementInspector
from assistant.filesystem import AttachmentsExtension
from assistant.response.utils.workbench_messages import (
    compute_tokens_from_workbench_messages,
    get_workbench_messages,
    workbench_message_to_oai_messages,
)

logger = logging.getLogger(__name__)


async def _get_final_index(
    context: ConversationContext,
    attachments_extension: AttachmentsExtension,
    token_window: int,
) -> int:
    """
    Determines the final index that we want to make any context management changes to
    based on the token window. Essentially the final chunk of max_chunk_size tokens we want to leave alone.
    """
    messages = await get_workbench_messages(context, attachments_extension)
    participants_response = await context.get_participants(include_inactive=True)

    # Start from the end and work backwards
    for i in range(len(messages.messages) - 1, -1, -1):
        # Create a subset of messages from index i to the end
        subset_messages = messages.model_copy(deep=True)
        subset_messages.messages = subset_messages.messages[i:]

        current_tokens = await compute_tokens_from_workbench_messages(
            context, subset_messages, [], participants_response
        )

        # If we exceed the token window, the previous index is our answer
        if current_tokens > token_window:
            return min(i + 1, len(messages.messages) - 1)

    return 0


async def complete_context_management(
    context: ConversationContext,
    config: AssistantConfigModel,
    attachments_extension: AttachmentsExtension,
    context_management_inspector: ContextManagementInspector,
    tools: list[ChatCompletionToolParam],
) -> list[ChatCompletionMessageParam]:
    # TODO: The telemetry doesn't work quite right.
    # context_management_inspector.reset_telemetry(context.id)
    cm_telemetry = context_management_inspector.get_telemetry(context.id)

    # Hyperparameters
    max_total_tokens_from_config = config.orchestration.prompts.max_total_tokens
    max_total_tokens = (
        int(config.generative_ai_client_config.request_config.max_tokens * 0.95)
        if max_total_tokens_from_config == -1
        else max_total_tokens_from_config
    )
    token_window_from_config = config.orchestration.prompts.token_window
    token_window = int(max_total_tokens * 0.2) if token_window_from_config == -1 else token_window_from_config
    target_token_count = max_total_tokens - token_window
    data_tools = ["view", "search", "click_link"]

    messages = await get_workbench_messages(context, attachments_extension)
    participants_response = await context.get_participants(include_inactive=True)

    current_tokens = await compute_tokens_from_workbench_messages(context, messages, tools, participants_response)
    cm_telemetry.total_context_tokens = current_tokens

    if current_tokens > max_total_tokens:
        logger.info(f"Token budget exceeded: {current_tokens} > {max_total_tokens}. Applying context management.")
    else:
        participants_response = await context.get_participants(include_inactive=True)
        oai_messages = await workbench_message_to_oai_messages(context, messages, participants_response)
        cm_telemetry.after_context_management_tokens = current_tokens
        cm_telemetry.final_messages = oai_messages
        return oai_messages

    # Heuristic Stage
    i = 0
    s = await _get_final_index(context, attachments_extension, token_window)
    # Start from all messages (skipping first system msg), and remove/truncate until we are under the target token count.
    messages_list = messages.messages
    messages_idx_for_removal = []
    while i < s:
        # Check if we are under the token budget yet
        current_tokens = await compute_tokens_from_workbench_messages(
            context, messages, tools, participants_response, messages_idx_for_removal
        )
        if current_tokens <= target_token_count:
            break

        # Apply rules to messages
        # First rules on tool messages. If assistant called a tool, iterate until we find the corresponding tool message
        if messages_list[i].sender.participant_id == context.assistant.id and messages_list[i].metadata.get(
            "tool_calls", None
        ):
            j = i + 1
            tool_message = None
            for j in range(i + 1, len(messages_list)):
                if messages_list[j].metadata.get("tool_result") is not None:
                    tool_message = messages_list[j]
                    break
            if tool_message:
                tool_result = tool_message.metadata.get("tool_result")
                tool_calls = tool_message.metadata.get("tool_calls", [])
                if tool_result is not None and len(tool_calls) > 0:
                    tool_call = tool_calls[0]
                    tool_name = tool_call.get("name", None)
                    # If data tool, replace with "call the tool again"
                    if tool_name in data_tools:
                        # Replace the tool call with instructions on how to get the content back.
                        tool_message.metadata["tool_result"]["content"] = (
                            "The content of this tool call result has been removed due to token limits. If you need it, call the tool again."
                        )
                        cm_telemetry.data_tool_calls_truncated += 1
                    else:
                        # If other tool, remove it
                        messages_idx_for_removal.append(i)
                        messages_idx_for_removal.append(j)
                        cm_telemetry.tool_calls_removed += 1
                # TODO: this will go wrong if the corresponding tool message is not the next message.
                i = j + 1
                continue
            else:
                raise ValueError("Tool message not found for assistant message.")
        # If attachment, replace with call view(<filename>)
        elif messages_list[i].filenames:
            filenames = messages_list[i].filenames
            for filename_idx in range(len(filenames)):
                if current_tokens > target_token_count:
                    # Replace the attachment with instructions on how to get it back.
                    messages_list[i].metadata["filename_to_content"][filenames[filename_idx]] = (
                        f"The content of this file has been removed to due token limits. Call view({filenames[filename_idx]}) to retrieve the current content."
                    )
                    cm_telemetry.attachments_truncated += 1
                    # Compute tokens again to prevent removing more than necessary.
                    current_tokens = await compute_tokens_from_workbench_messages(
                        context, messages, tools, participants_response, messages_idx_for_removal
                    )
                else:
                    break

            i += 1
            continue
        i += 1

    # Eviction Stage
    # If we are still over the limit, we start removing chunks of conversation messages
    # Look up the pre-computed chunk corresponding to the first message.
    # If it doesn't exist, compute it now
    # Remove all of its corresponding messages from the conversation.
    # Check if we are over the limit and continue
    current_tokens = await compute_tokens_from_workbench_messages(
        context, messages, tools, participants_response, messages_idx_for_removal
    )
    cm_telemetry.tokens_after_heuristic_stage = current_tokens
    if len(messages.messages) > 3 and current_tokens > target_token_count:
        compaction_data = await get_compaction_data(context)
        # Maps messages to their compaction chunk IDs
        compaction_map = compaction_data.compaction_mapping()
        # Starting from the first message, determine which chunk it belongs and then remove that **entire** chunk.
        # Then, if we are still over the limit, look at the first, next remaining and do the same operation.

        i = 0
        while i < len(messages.messages) and current_tokens > target_token_count:
            # Skip if already marked for removal
            if i in messages_idx_for_removal:
                i += 1
                continue

            message_id = messages.messages[i].id

            # Check if this message belongs to a compacted chunk
            if message_id in compaction_map:
                chunk_id = compaction_map[message_id]

                # Find all messages in this chunk and mark them for removal
                chunk_data = compaction_data.compaction_data.get(chunk_id)
                if chunk_data:
                    cm_telemetry.chunks_evicted += 1
                    for conv_message_id in chunk_data.conv_message_ids:
                        # Find the index of this message and mark for removal
                        for j, msg in enumerate(messages.messages):
                            if msg.id == conv_message_id and j not in messages_idx_for_removal:
                                messages_idx_for_removal.append(j)

                    # Recompute tokens after removing this chunk
                    current_tokens = await compute_tokens_from_workbench_messages(
                        context, messages, tools, participants_response, messages_idx_for_removal
                    )

            i += 1

    # Remove the messages that are marked for removal
    new_messages = []
    for i in range(len(messages.messages)):
        if i not in messages_idx_for_removal:
            new_messages.append(messages.messages[i])
    messages.messages = new_messages

    participants_response = await context.get_participants(include_inactive=True)
    oai_messages = await workbench_message_to_oai_messages(context, messages, participants_response)

    # Update telemetry with final state
    cm_telemetry.after_context_management_tokens = await compute_tokens_from_workbench_messages(
        context, messages, tools, participants_response
    )
    cm_telemetry.final_messages = oai_messages

    return oai_messages
