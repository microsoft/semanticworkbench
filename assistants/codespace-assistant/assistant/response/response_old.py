# import logging
# import time
# from contextlib import AsyncExitStack
# from typing import Any, List

# import deepmerge
# from assistant_extensions.ai_clients.model import CompletionMessage
# from assistant_extensions.artifacts import ArtifactsExtension
# from assistant_extensions.attachments import AttachmentsExtension
# from mcp import ClientSession, Tool
# from semantic_workbench_api_model.workbench_model import (
#     MessageType,
#     NewConversationMessage,
# )
# from semantic_workbench_assistant.assistant_app import ConversationContext

# from ..config import AssistantConfigModel
# from ..extensions.tools import establish_mcp_sessions, handle_tool_action, retrieve_tools_from_sessions
# from .utils import (
#     build_system_message_content,
#     conversation_message_to_completion_messages,
#     get_history_messages,
#     get_response_duration_message,
#     get_token_usage_message,
#     initialize_response_provider,
#     inject_attachments_inline,
#     num_tokens_from_messages,
# )

# logger = logging.getLogger(__name__)


# async def respond_to_conversation(
#     artifacts_extension: ArtifactsExtension,
#     attachments_extension: AttachmentsExtension,
#     context: ConversationContext,
#     config: AssistantConfigModel,
#     metadata: dict[str, Any] = {},
#     config_file: str = "mcp_servers_config.json",
# ) -> None:
#     """
#     Respond to a conversation message using dynamically loaded MCP servers with support for multiple tool invocations.
#     """

#     async with AsyncExitStack() as stack:
#         mcp_sessions: List[ClientSession] = []
#         mcp_tools: List[Tool] = []

#         if config.extensions_config.tools.enabled:
#             mcp_sessions = await establish_mcp_sessions(config_file, stack)
#             if not mcp_sessions:
#                 await context.send_messages(
#                     NewConversationMessage(
#                         content="Unable to connect to any MCP servers. Please ensure the servers are running.",
#                         message_type=MessageType.notice,
#                         metadata=metadata,
#                     )
#                 )
#                 return

#             # Retrieve tools from the MCP sessions
#             mcp_tools = await retrieve_tools_from_sessions(mcp_sessions)

#         # Initialize the response provider based on configuration
#         response_provider = initialize_response_provider(config, artifacts_extension, context)

#         # Get the request configuration for the AI client
#         request_config = config.ai_client_config.request_config

#         # Define the metadata key for any metadata created within this method
#         method_metadata_key = "respond_to_conversation"

#         # Track the start time of the response generation
#         response_start_time = time.time()

#         # Get the list of conversation participants
#         participants_response = await context.get_participants(include_inactive=True)
#         participants = participants_response.participants

#         # Establish a token to be used by the AI model to indicate no response
#         silence_token = "{{SILENCE}}"

#         # Build system message content
#         system_message_content = build_system_message_content(config, context, participants, silence_token)

#         # Initialize the completion messages with the system message
#         completion_messages: List[CompletionMessage] = [
#             CompletionMessage(
#                 role="system",
#                 content=system_message_content,
#             )
#         ]

#         token_count = 0

#         # Calculate the token count for the messages so far
#         result = await num_tokens_from_messages(
#             context=context,
#             response_provider=response_provider,
#             messages=completion_messages,
#             model=request_config.model,
#             metadata=metadata,
#             metadata_key="system_message",
#         )
#         if result is not None:
#             token_count += result.count
#         else:
#             return

#         # Generate the attachment messages
#         attachment_messages = await attachments_extension.get_completion_messages_for_attachments(
#             context,
#             config=config.extensions_config.attachments,
#         )
#         result = await num_tokens_from_messages(
#             context=context,
#             response_provider=response_provider,
#             messages=attachment_messages,
#             model=request_config.model,
#             metadata=metadata,
#             metadata_key="attachment_messages",
#         )
#         if result is not None:
#             token_count += result.count
#         else:
#             return

#         # Calculate available tokens
#         available_tokens = request_config.max_tokens - request_config.response_tokens

#         # Get history messages
#         history_messages = await get_history_messages(
#             response_provider=response_provider,
#             context=context,
#             participants=participants_response.participants,
#             converter=conversation_message_to_completion_messages,
#             model=request_config.model,
#             token_limit=available_tokens - token_count,
#         )

#         # Inject or append attachment messages
#         if config.use_inline_attachments:
#             history_messages = inject_attachments_inline(history_messages, attachment_messages)
#         else:
#             completion_messages.extend(attachment_messages)

#         # Add history messages
#         completion_messages.extend(history_messages)

#         # Check token count
#         result = await num_tokens_from_messages(
#             context=context,
#             response_provider=response_provider,
#             messages=completion_messages,
#             model=request_config.model,
#             metadata=metadata,
#             metadata_key=method_metadata_key,
#         )
#         if result is not None:
#             estimated_token_count = result.count
#             if estimated_token_count > request_config.max_tokens:
#                 await context.send_messages(
#                     NewConversationMessage(
#                         content=(
#                             f"You've exceeded the token limit of {request_config.max_tokens} in this conversation "
#                             f"({estimated_token_count}). This assistant does not support recovery from this state. "
#                             "Please start a new conversation and let us know you ran into this."
#                         ),
#                         message_type=MessageType.chat,
#                         metadata=metadata,
#                     )
#                 )
#                 return
#         else:
#             return

#         # Initialize variables to prevent "possibly unbound" warnings
#         completion_total_tokens: int = 0
#         content: str = ""
#         message_type: MessageType = MessageType.chat
#         final_response: str = ""  # New variable to accumulate responses

#         # Initialize a loop control variable
#         max_steps = config.extensions_config.tools.max_steps
#         completed_within_max_steps = False
#         step_count = 0

#         while step_count < max_steps:
#             step_count += 1

#             # Generate AI response
#             try:
#                 response_result = await response_provider.get_response(
#                     config=config,
#                     messages=completion_messages,
#                     metadata_key=f"{method_metadata_key}:request:step_{step_count}",
#                     mcp_tools=mcp_tools,
#                 )
#             except Exception as e:
#                 logger.exception(f"Error generating AI response: {e}")
#                 await context.send_messages(
#                     NewConversationMessage(
#                         content="An error occurred while generating your response.",
#                         message_type=MessageType.notice,
#                         metadata=metadata,
#                     )
#                 )
#                 return

#             # Safely assign values to prevent unbound issues
#             content = response_result.content if response_result.content else ""
#             tool_actions = response_result.tool_actions if response_result.tool_actions else []
#             message_type = response_result.message_type if response_result.message_type else MessageType.chat
#             completion_total_tokens = (
#                 response_result.completion_total_tokens if response_result.completion_total_tokens else 0
#             )

#             deepmerge.always_merger.merge(metadata, response_result.metadata)

#             # Append the AI's response to the messages
#             if content.replace(" ", "") != silence_token:
#                 final_response += content + "\n"

#                 # Add the AI's response to the messages
#                 completion_messages.append(
#                     CompletionMessage(
#                         role="assistant",
#                         content=content,
#                     )
#                 )

#             if len(tool_actions) == 0:
#                 # No tool actions, exit the loop
#                 completed_within_max_steps = True
#                 break

#             # Handle tool actions
#             tool_call_count = 0
#             for tool_action in tool_actions:
#                 tool_call_count += 1
#                 try:
#                     tool_action_result = await handle_tool_action(
#                         mcp_sessions,
#                         tool_action,
#                         mcp_tools,
#                         f"{method_metadata_key}:request:step_{step_count}:tool_action_{tool_call_count}",
#                     )
#                 except Exception as e:
#                     logger.exception(f"Error handling tool action: {e}")
#                     await context.send_messages(
#                         NewConversationMessage(
#                             content="An error occurred while handling the tool action.",
#                             message_type=MessageType.notice,
#                             metadata=metadata,
#                         )
#                     )
#                     return

#                 # Wrap tool_action in ```tool_action<data>```
#                 tool_action_formatted = f"```tool_action\n{tool_action_result.content}\n```"
#                 final_response += tool_action_formatted + "\n"

#                 # Update content and metadata with tool action result
#                 deepmerge.always_merger.merge(metadata, tool_action_result.metadata)

#                 # Append the tool's response to the messages
#                 completion_messages.append(
#                     CompletionMessage(
#                         # FIXME: should use role "tool", but need to make sure that prior message has tool_calls prop for OpenAI
#                         role="user",
#                         tool_call_id=tool_action.id,
#                         content=tool_action_result.content,
#                     )
#                 )

#         # Create the footer items for the response
#         footer_items = []

#         # Add the token usage message to the footer items
#         if completion_total_tokens > 0:
#             footer_items.append(get_token_usage_message(request_config.max_tokens, completion_total_tokens))

#         # Track the end time of the response generation and calculate duration
#         response_end_time = time.time()
#         response_duration = response_end_time - response_start_time

#         # Add the response duration to the footer items
#         footer_items.append(get_response_duration_message(response_duration))

#         # Update the metadata with the footer items
#         deepmerge.always_merger.merge(
#             metadata,
#             {
#                 "footer_items": footer_items,
#             },
#         )

#         if final_response:
#             if not completed_within_max_steps:
#                 # Add a note at the end of the content to indicate such
#                 final_response += "\n\n" + config.extensions_config.tools.max_steps_truncation_message

#             # Handle silence token
#             if final_response.replace(" ", "") == silence_token:
#                 # If debug output is enabled, notify that the assistant chose to remain silent
#                 if config.enable_debug_output:
#                     # Add debug metadata to indicate the assistant chose to remain silent
#                     deepmerge.always_merger.merge(
#                         metadata,
#                         {
#                             "debug": {
#                                 method_metadata_key: {
#                                     "silence_token": True,
#                                 },
#                             },
#                             "attribution": "debug output",
#                             "generated_content": False,
#                         },
#                     )
#                     # Send a notice message to the conversation
#                     await context.send_messages(
#                         NewConversationMessage(
#                             message_type=MessageType.notice,
#                             content="[assistant chose to remain silent]",
#                             metadata=metadata,
#                         )
#                     )
#                 return  # Exit the function if the assistant remains silent

#             # Override message type if content starts with '/'
#             if final_response.startswith("/"):
#                 message_type = MessageType.command_response

#         # Send the final accumulated response to the conversation
#         await context.send_messages(
#             NewConversationMessage(
#                 content=final_response or "[no response from AI]",
#                 message_type=message_type,
#                 metadata=metadata,
#             )
#         )

#         # Send token usage warning if applicable
#         if completion_total_tokens and config.high_token_usage_warning.enabled:
#             token_count_for_warning = request_config.max_tokens * (config.high_token_usage_warning.threshold / 100)
#             if completion_total_tokens > token_count_for_warning:
#                 warning_content = (
#                     f"{config.high_token_usage_warning.message}\n\nTotal tokens used: {completion_total_tokens}"
#                 )
#                 await context.send_messages(
#                     NewConversationMessage(
#                         content=warning_content,
#                         message_type=MessageType.notice,
#                         metadata={
#                             "debug": {
#                                 "high_token_usage_warning": {
#                                     "completion_total_tokens": completion_total_tokens,
#                                     "threshold": config.high_token_usage_warning.threshold,
#                                     "token_count_for_warning": token_count_for_warning,
#                                 }
#                             },
#                             "attribution": "system",
#                         },
#                     )
#                 )
