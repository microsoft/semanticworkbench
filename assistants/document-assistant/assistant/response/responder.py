# Copyright (c) Microsoft. All rights reserved.

import asyncio
import json
import logging
import time
from contextlib import AsyncExitStack
from typing import Any, Awaitable, Callable

import deepmerge
import pendulum
from assistant_extensions.attachments import get_attachments
from assistant_extensions.chat_context_toolkit.message_history import (
    chat_context_toolkit_message_provider_for,
    construct_attachment_summarizer,
)
from assistant_extensions.chat_context_toolkit.virtual_filesystem import (
    archive_file_source_mount,
)
from assistant_extensions.mcp import (
    ExtendedCallToolRequestParams,
    MCPClientSettings,
    MCPServerConnectionError,
    OpenAISamplingHandler,
    establish_mcp_sessions,
    get_enabled_mcp_server_configs,
    get_mcp_server_prompts,
    list_roots_callback_for,
    refresh_mcp_sessions,
    sampling_message_to_chat_completion_message,
)
from chat_context_toolkit.history import NewTurn, apply_budget_to_history_messages
from chat_context_toolkit.virtual_filesystem import FileEntry, VirtualFileSystem
from liquid import render
from mcp import SamplingMessage, ServerNotification
from mcp.types import (
    TextContent,
)
from openai.types.chat import (
    ChatCompletionMessageParam,
    ChatCompletionSystemMessageParam,
    ChatCompletionToolParam,
)
from openai_client import (
    create_client,
    num_tokens_from_message,
    num_tokens_from_messages,
    num_tokens_from_tools,
)
from pydantic import BaseModel
from semantic_workbench_api_model import workbench_model
from semantic_workbench_api_model.workbench_model import (
    ConversationMessage,
    MessageType,
    NewConversationMessage,
    UpdateParticipant,
)
from semantic_workbench_assistant.assistant_app import (
    ConversationContext,
)

from assistant.config import AssistantConfigModel
from assistant.context_management.inspector import ContextManagementInspector
from assistant.filesystem import (
    EDIT_TOOL_DESCRIPTION_HOSTED,
    EDIT_TOOL_DESCRIPTION_LOCAL,
    VIEW_TOOL_OBJ,
    AttachmentsExtension,
)
from assistant.filesystem._file_sources import attachments_file_source_mount, editable_documents_file_source_mount
from assistant.filesystem._filesystem import _files_drive_for_context
from assistant.filesystem._prompts import ARCHIVES_ADDON_PROMPT, FILES_PROMPT, LS_TOOL_OBJ
from assistant.guidance.dynamic_ui_inspector import get_dynamic_ui_state, update_dynamic_ui_state
from assistant.guidance.guidance_prompts import DYNAMIC_UI_TOOL_NAME, DYNAMIC_UI_TOOL_OBJ
from assistant.response.completion_handler import handle_completion
from assistant.response.models import StepResult
from assistant.response.prompts import ORCHESTRATION_SYSTEM_PROMPT, tool_abbreviations
from assistant.response.utils import get_ai_client_configs, get_completion, get_openai_tools_from_mcp_sessions
from assistant.response.utils.tokens_tiktoken import TokenizerOpenAI
from assistant.whiteboard import notify_whiteboard

logger = logging.getLogger(__name__)


class ConversationMessageMetadata(BaseModel):
    associated_filenames: str | None = None


# region Initialization


class ConversationResponder:
    def __init__(
        self,
        message: ConversationMessage,
        context: ConversationContext,
        config: AssistantConfigModel,
        metadata: dict[str, Any],
        attachments_extension: AttachmentsExtension,
        context_management_inspector: ContextManagementInspector,
    ) -> None:
        self.message = message
        self.context = context
        self.config = config
        self.metadata = metadata
        self.attachments_extension = attachments_extension
        self.context_management_inspector = context_management_inspector
        self.latest_telemetry = context_management_inspector.get_telemetry(context.id)

        self.stack = AsyncExitStack()

        # Constants
        self.token_model = "gpt-4o"
        # The maximum number of tokens that each sub-component of the system prompt can have.
        self.max_system_prompt_component_tokens = 2000
        # Max number of tokens that should go into a request
        max_total_tokens_from_config = self.config.orchestration.prompts.max_total_tokens
        self.max_total_tokens = (
            int(self.config.generative_ai_client_config.request_config.max_tokens * 0.95)
            if max_total_tokens_from_config == -1
            else max_total_tokens_from_config
        )

        token_window_from_config = self.config.orchestration.prompts.token_window
        self.token_window = (
            int(self.max_total_tokens * 0.2) if token_window_from_config == -1 else token_window_from_config
        )

        self.tokenizer = TokenizerOpenAI(model=self.token_model)

        # Chat Context Toolkit
        self.history_turn = NewTurn()
        self.virtual_filesystem = VirtualFileSystem(
            mounts=[
                archive_file_source_mount(context),
                attachments_file_source_mount(context, attachments_extension),
                editable_documents_file_source_mount(context, _files_drive_for_context),
            ],
        )

    @classmethod
    async def create(
        cls,
        message: ConversationMessage,
        context: ConversationContext,
        config: AssistantConfigModel,
        metadata: dict[str, Any],
        attachments_extension: AttachmentsExtension,
        context_management_inspector: ContextManagementInspector,
    ) -> "ConversationResponder":
        responder = cls(message, context, config, metadata, attachments_extension, context_management_inspector)
        await responder._setup()
        return responder

    async def _setup(self) -> None:
        await self._setup_mcp()

    # endregion

    # region Responding Loop

    async def respond_to_conversation(self) -> None:
        interrupted = False
        encountered_error = False
        completed_within_max_steps = False
        step_count = 0
        while step_count < self.config.orchestration.options.max_steps:
            step_count += 1
            self.mcp_sessions = await refresh_mcp_sessions(self.mcp_sessions, self.stack)

            # Check to see if we should interrupt our flow
            last_message = await self.context.get_messages(limit=1, message_types=[MessageType.chat])
            if step_count > 1 and last_message.messages[0].sender.participant_id != self.context.assistant.id:
                # The last message was from a sender other than the assistant, so we should
                # interrupt our flow as this would have kicked off a new response from this
                # assistant with the new message in mind and that process can decide if it
                # should continue with the current flow or not.
                interrupted = True
                logger.info("Response interrupted by user message.")
                break

            step_result = await self._step(step_count)

            match step_result.status:
                case "final":
                    completed_within_max_steps = True
                    break
                case "error":
                    encountered_error = True
                    break

        # If the response did not complete within the maximum number of steps, send a message to the user
        if not completed_within_max_steps and not encountered_error and not interrupted:
            await self.context.send_messages(
                NewConversationMessage(
                    content=self.config.orchestration.options.max_steps_truncation_message,
                    message_type=MessageType.notice,
                    metadata=self.metadata,
                )
            )
            logger.info("Response stopped early due to maximum steps.")

        await self._cleanup()

    # endregion

    # region Response Step

    async def _step(self, step_count) -> StepResult:
        step_result = StepResult(status="continue", metadata=self.metadata.copy())

        response_start_time = time.time()

        tools, chat_message_params = await self._construct_prompt()

        await self.context_management_inspector.update_state(self.context)

        self.sampling_handler.message_processor = await self._update_sampling_message_processor(
            chat_history=chat_message_params
        )

        await notify_whiteboard(
            context=self.context,
            server_config=self.config.orchestration.hosted_mcp_servers.memory_whiteboard,
            attachment_messages=[],
            chat_messages=chat_message_params[1:],
        )

        async with create_client(self.config.generative_ai_client_config.service_config) as client:
            async with self.context.set_status("thinking..."):
                try:
                    # If user guidance is enabled, we transparently run two LLM calls with very similar parameters.
                    # One is the mainline LLM call for the orchestration, the other is identically expect it forces the LLM to
                    # call the DYNAMIC_UI_TOOL_NAME function to generate UI elements right after a user message is sent (the first step).
                    # This is done to only interrupt the user letting them know when the LLM deems it to be necessary.
                    # Otherwise, UI elements are generated in the background.
                    # Finally, we use the same parameters for both calls so that LLM understands the capabilities of the assistant when generating UI elements.
                    deepmerge.always_merger.merge(
                        self.metadata,
                        {
                            "debug": {
                                f"respond_to_conversation:step_{step_count}": {
                                    "request": {
                                        "model": self.config.generative_ai_client_config.request_config.model,
                                        "messages": chat_message_params,
                                        "max_tokens": self.config.generative_ai_client_config.request_config.response_tokens,
                                        "tools": tools,
                                    },
                                },
                            },
                        },
                    )
                    completion_dynamic_ui = None
                    if self.config.orchestration.guidance.enabled and step_count == 1:
                        dynamic_ui_task = get_completion(
                            client,
                            self.config.generative_ai_client_config.request_config,
                            chat_message_params,
                            tools,
                            tool_choice=DYNAMIC_UI_TOOL_NAME,
                        )
                        completion_task = get_completion(
                            client, self.config.generative_ai_client_config.request_config, chat_message_params, tools
                        )
                        completion_dynamic_ui, completion = await asyncio.gather(dynamic_ui_task, completion_task)
                    else:
                        completion = await get_completion(
                            client, self.config.generative_ai_client_config.request_config, chat_message_params, tools
                        )

                except Exception as e:
                    logger.exception(f"exception occurred calling openai chat completion: {e}")
                    deepmerge.always_merger.merge(
                        step_result.metadata,
                        {
                            "debug": {
                                f"respond_to_conversation:step_{step_count}": {
                                    "error": str(e),
                                },
                            },
                        },
                    )
                    await self.context.send_messages(
                        NewConversationMessage(
                            content="An error occurred while calling the OpenAI API. Is it configured correctly?"
                            " View the debug inspector for more information.",
                            message_type=MessageType.notice,
                            metadata=step_result.metadata,
                        )
                    )
                    step_result.status = "error"
                    return step_result

        if self.config.orchestration.guidance.enabled and completion_dynamic_ui:
            # Check if the regular request generated the DYNAMIC_UI_TOOL_NAME
            called_dynamic_ui_tool = False
            if completion.choices[0].message.tool_calls:
                for tool_call in completion.choices[0].message.tool_calls:
                    if tool_call.function.name == DYNAMIC_UI_TOOL_NAME:
                        called_dynamic_ui_tool = True
                        # Open the dynamic UI inspector tab
                        await self.context.send_conversation_state_event(
                            workbench_model.AssistantStateEvent(
                                state_id="dynamic_ui",
                                event="focus",
                                state=None,
                            )
                        )

            # If it did, completely ignore the special completion. Otherwise, use it to generate UI for this turn
            if not called_dynamic_ui_tool:
                tool_calls = completion_dynamic_ui.choices[0].message.tool_calls
                # Otherwise, use it generate the UI for this return
                if tool_calls:
                    tool_call = tool_calls[0]
                    tool_call = ExtendedCallToolRequestParams(
                        id=tool_call.id,
                        name=tool_call.function.name,
                        arguments=json.loads(
                            tool_call.function.arguments,
                        ),
                    )  # Check if any ui_elements were generated and abort early if not
                    if tool_call.arguments and tool_call.arguments.get("ui_elements", []):
                        await update_dynamic_ui_state(self.context, tool_call.arguments)

        step_result = await handle_completion(
            step_result,
            completion,
            self.mcp_sessions,
            self.context,
            self.config.generative_ai_client_config.request_config,
            f"respond_to_conversation:step_{step_count}",
            response_start_time,
            self.config.orchestration.guidance.enabled,
            self.virtual_filesystem,
        )
        return step_result

    # endregion

    # region Prompt Construction

    async def _construct_prompt(self) -> tuple[list, list[ChatCompletionMessageParam]]:
        # Set tools
        tools = []
        if self.config.orchestration.guidance.enabled:
            tools.append(DYNAMIC_UI_TOOL_OBJ)
        tools.extend(
            get_openai_tools_from_mcp_sessions(self.mcp_sessions, self.config.orchestration.tools_disabled) or []
        )
        # Remove any view tool that was added by an MCP server and replace it with ours.
        # Also remove the list_working_directory tool because we will automatically inject available files into the system prompt.
        tools = [tool for tool in tools if tool["function"]["name"] not in ["view", "list_working_directory", "ls"]]
        tools.append(VIEW_TOOL_OBJ)
        tools.append(LS_TOOL_OBJ)
        # Override the description of the edit_file depending on the environment
        tools = self._override_edit_file_description(tools)

        # Note: Currently assuming system prompt will fit into the token budget.
        # Start constructing main system prompt
        # Inject the {{knowledge_cutoff}} and {{current_date}} placeholders
        main_system_prompt = render(
            ORCHESTRATION_SYSTEM_PROMPT,
            **{
                "knowledge_cutoff": self.config.orchestration.prompts.knowledge_cutoff,
                "current_date": pendulum.now(tz="America/Los_Angeles").format("YYYY-MM-DD"),
            },
        )

        # Construct key parts of the system messages which are core capabilities.
        # Best practice is to have these start with a ## <heading content>
        # User Guidance and & Dynamic UI Generation
        if self.config.orchestration.guidance.enabled:
            dynamic_ui_system_prompt = self.tokenizer.truncate_str(
                await self._construct_dynamic_ui_system_prompt(),
                10000,  # For now, don't limit this that much
            )
            main_system_prompt += "\n\n" + dynamic_ui_system_prompt.strip()

        # Filesystem System Prompt
        ls_result = await self._construct_filesystem_system_prompt()
        filesystem_system_prompt = self.tokenizer.truncate_str(ls_result, max_len=10000)
        main_system_prompt += "\n\n" + filesystem_system_prompt.strip()

        # Add specific guidance from MCP servers
        mcp_prompts = await get_mcp_server_prompts(self.mcp_sessions)
        mcp_prompt_string = self.tokenizer.truncate_str(
            "## MCP Servers" + "\n\n" + "\n\n".join(mcp_prompts), self.max_system_prompt_component_tokens
        )
        main_system_prompt += "\n\n" + mcp_prompt_string.strip()

        # Always append the guardrails postfix at the end.
        main_system_prompt += "\n\n" + self.config.orchestration.prompts.guardrails_prompt.strip()
        self.latest_telemetry.system_prompt = main_system_prompt

        main_system_prompt = ChatCompletionSystemMessageParam(
            role="system",
            content=main_system_prompt,
        )

        message_provider = chat_context_toolkit_message_provider_for(
            context=self.context,
            tool_abbreviations=tool_abbreviations,
            attachments=list(
                await get_attachments(
                    self.context,
                    summarizer=construct_attachment_summarizer(
                        service_config=self.config.generative_ai_fast_client_config.service_config,
                        request_config=self.config.generative_ai_fast_client_config.request_config,
                    ),
                )
            ),
        )
        system_prompt_token_count = num_tokens_from_message(main_system_prompt, model="gpt-4o")
        tool_token_count = num_tokens_from_tools(tools, model="gpt-4o")
        message_history_token_budget = (
            self.config.orchestration.prompts.max_total_tokens
            - system_prompt_token_count
            - tool_token_count
            - self.config.generative_ai_client_config.request_config.response_tokens
        )
        budgeted_messages_result = await apply_budget_to_history_messages(
            turn=self.history_turn,
            token_budget=message_history_token_budget,
            token_counter=lambda messages: num_tokens_from_messages(messages=messages, model="gpt-4o"),
            message_provider=message_provider,
        )
        chat_history: list[ChatCompletionMessageParam] = list(budgeted_messages_result.messages)
        chat_history.insert(0, main_system_prompt)

        logger.info("The system prompt has been constructed.")
        # Update telemetry for inspector
        self.latest_telemetry.system_prompt_tokens = system_prompt_token_count
        self.latest_telemetry.tool_tokens = tool_token_count
        self.latest_telemetry.message_tokens = num_tokens_from_messages(messages=chat_history, model="gpt-4o")
        self.latest_telemetry.total_context_tokens = (
            system_prompt_token_count + tool_token_count + self.latest_telemetry.message_tokens
        )
        self.latest_telemetry.final_messages = chat_history

        return tools, chat_history

    async def _construct_dynamic_ui_system_prompt(self) -> str:
        current_dynamic_ui_elements = await get_dynamic_ui_state(context=self.context)

        if not current_dynamic_ui_elements:
            current_dynamic_ui_elements = "No dynamic UI elements have been generated yet. Consider generating some."

        system_prompt = "## On Dynamic UI Elements\n"
        system_prompt += "\n" + self.config.orchestration.guidance.prompt
        system_prompt += "\n" + str(current_dynamic_ui_elements)
        return system_prompt

    async def _construct_filesystem_system_prompt(self) -> str:
        """Constructs the filesystem system prompt with available files.

        Builds a system prompt that includes:
        1. FILES_PROMPT with attachments and editable_documents (up to 25 files)
        2. ARCHIVES_ADDON_PROMPT (if archives exist)
        3. Archives files listing (up to 25 files)

        Files are sorted by timestamp (newest first), limited to 25 per category,
        then sorted alphabetically by path.

        This is an example of what gets added after the FILES_PROMPT:
        -r-- path2.pdf [File content summary: <summary>]
        -rw- path3.txt [File content summary: No summary available yet, use the context available to determine the use of this file]
        """
        # Get all file entries
        attachments_entries = list(await self.virtual_filesystem.list_directory(path="/attachments"))
        editable_documents_entries = list(await self.virtual_filesystem.list_directory(path="/editable_documents"))
        archives_entries = list(await self.virtual_filesystem.list_directory(path="/archives"))
        
        # Separate regular files from archives
        regular_files = [entry for entry in (attachments_entries + editable_documents_entries) if isinstance(entry, FileEntry)]
        archives_files = [entry for entry in archives_entries if isinstance(entry, FileEntry)]

        # TODO: Better ranking algorithm
        # order the regular files by timestamp, newest first
        regular_files.sort(key=lambda f: f.timestamp, reverse=True)
        # take the top 25 regular files
        regular_files = regular_files[:25]
        # order them alphabetically by path
        regular_files.sort(key=lambda f: f.path.lower())

        # Start with FILES_PROMPT and add attachments/editable_documents
        system_prompt = FILES_PROMPT + "\n"
        if not regular_files:
            system_prompt += "\nNo files are currently available."

        for file in regular_files:
            # Format permissions: -rw- for read_write, -r-- for read
            permissions = "-rw-" if file.permission == "read_write" else "-r--"
            # Use the file description as the summary, or provide a default message
            summary = (
                file.description
                if file.description
                else "No summary available yet, use the context available to determine the use of this file"
            )
            system_prompt += f"{permissions} {file.path} [File content summary: {summary}]\n"

        # Add ARCHIVES_ADDON_PROMPT if there are archives
        if archives_files:
            system_prompt += "\n" + ARCHIVES_ADDON_PROMPT + "\n"
            
            # order the archives files by timestamp, newest first
            archives_files.sort(key=lambda f: f.timestamp, reverse=True)
            # take the top 25 archives files
            archives_files = archives_files[:25]
            # order them alphabetically by path
            archives_files.sort(key=lambda f: f.path.lower())
            
            for file in archives_files:
                # Format permissions: -rw- for read_write, -r-- for read
                permissions = "-rw-" if file.permission == "read_write" else "-r--"
                # Use the file description as the summary, or provide a default message
                summary = (
                    file.description
                    if file.description
                    else "No summary available yet, use the context available to determine the use of this file"
                )
                system_prompt += f"{permissions} {file.path} [File content summary: {summary}]\n"

        return system_prompt

    def _override_edit_file_description(self, tools: list[ChatCompletionToolParam]) -> list[ChatCompletionToolParam]:
        """
        Override the edit_file description based on the root (the one that indicates the hosted env, otherwise assume the local env).
        """
        try:
            # Get the root of the filesystem-edit tool
            # Find the filesystem MCP by name
            filesystem_mcp = next(
                (mcp for mcp in self.mcp_sessions if mcp.config.server_config.key == "filesystem-edit"),
                None,
            )
            filesystem_root = None
            if filesystem_mcp:
                # Get the root of the filesystem-edit tool
                filesystem_root = next(
                    (root for root in filesystem_mcp.config.server_config.roots if root.name == "root"),
                    None,
                )

            edit_tool = next(
                (tool for tool in tools if tool["function"]["name"] == "edit_file"),
                None,
            )
            if filesystem_root and filesystem_root.uri == "file://workspace" and edit_tool:
                edit_tool["function"]["description"] = EDIT_TOOL_DESCRIPTION_HOSTED
            elif filesystem_root and edit_tool:
                edit_tool["function"]["description"] = EDIT_TOOL_DESCRIPTION_LOCAL
        except Exception:
            logger.exception("Failed to override edit_file description")
            return tools

        return tools

    # endregion

    # region MCP Sessions

    async def _update_sampling_message_processor(
        self,
        chat_history: list[ChatCompletionMessageParam],
    ) -> Callable[[list[SamplingMessage], int, str], Awaitable[list[ChatCompletionMessageParam]]]:
        """
        Constructs function that will inject context from the assistant into sampling calls from the MCP server if it requests it.
        Currently supports a custom message of:
        `{"variable": "history_messages"}` which will inject the chat history with attachments into the sampling call.
        """

        async def _sampling_message_processor(
            messages: list[SamplingMessage], available_tokens: int, model: str
        ) -> list[ChatCompletionMessageParam]:
            updated_messages: list[ChatCompletionMessageParam] = []

            for message in messages:
                if not isinstance(message.content, TextContent):
                    updated_messages.append(sampling_message_to_chat_completion_message(message))
                    continue

                # Determine if the message.content.text is a json payload
                content = message.content.text
                if not content.startswith("{") or not content.endswith("}"):
                    updated_messages.append(sampling_message_to_chat_completion_message(message))
                    continue

                # Attempt to parse the json payload
                try:
                    json_payload = json.loads(content)
                    variable = json_payload.get("variable")
                    match variable:
                        case "attachment_messages":
                            # Ignore this for now, as we are handling attachments in the main message
                            continue
                        case "history_messages":
                            # Always skip the first message in the chat history, as it is the system prompt
                            if len(chat_history) > 1:
                                updated_messages.extend(chat_history[1:])
                            continue
                        case _:
                            updated_messages.append(sampling_message_to_chat_completion_message(message))
                            continue
                except json.JSONDecodeError:
                    updated_messages.append(sampling_message_to_chat_completion_message(message))
                    continue

            return updated_messages

        return _sampling_message_processor

    async def _setup_mcp(self) -> None:
        generative_ai_client_config = get_ai_client_configs(self.config, "generative")
        reasoning_ai_client_config = get_ai_client_configs(self.config, "reasoning")

        sampling_handler = OpenAISamplingHandler(
            ai_client_configs=[
                generative_ai_client_config,
                reasoning_ai_client_config,
            ],
        )
        self.sampling_handler = sampling_handler

        async def message_handler(message) -> None:
            if isinstance(message, ServerNotification) and message.root.method == "notifications/message":
                await self.context.update_participant_me(UpdateParticipant(status=f"{message.root.params.data}"))

        client_resource_handler = self.attachments_extension.client_resource_handler_for(self.context)

        enabled_servers = get_enabled_mcp_server_configs(self.config.orchestration.mcp_servers)

        try:
            mcp_sessions = await establish_mcp_sessions(
                client_settings=[
                    MCPClientSettings(
                        server_config=server_config,
                        sampling_callback=self.sampling_handler.handle_message,
                        message_handler=message_handler,
                        list_roots_callback=list_roots_callback_for(context=self.context, server_config=server_config),
                        experimental_resource_callbacks=(
                            client_resource_handler.handle_list_resources,
                            client_resource_handler.handle_read_resource,
                            client_resource_handler.handle_write_resource,
                        ),
                    )
                    for server_config in enabled_servers
                ],
                stack=self.stack,
            )
            self.mcp_sessions = mcp_sessions
        except MCPServerConnectionError as e:
            await self.context.send_messages(
                NewConversationMessage(
                    content=f"Failed to connect to MCP server {e.server_config.key}: {e}",
                    message_type=MessageType.notice,
                    metadata=self.metadata,
                )
            )

    # endregion

    # region Misc

    async def _cleanup(self) -> None:
        await self.stack.aclose()

    # endregion
