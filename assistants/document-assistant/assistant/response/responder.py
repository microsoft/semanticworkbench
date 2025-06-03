import asyncio
import json
import logging
import time
from contextlib import AsyncExitStack
from typing import Any, Awaitable, Callable

import deepmerge
import pendulum
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
from liquid import render
from mcp import SamplingMessage, ServerNotification
from mcp.types import (
    TextContent,
)
from openai.types.chat import (
    ChatCompletionContentPartImageParam,
    ChatCompletionContentPartTextParam,
    ChatCompletionMessageParam,
    ChatCompletionSystemMessageParam,
    ChatCompletionToolParam,
    ChatCompletionUserMessageParam,
)
from openai.types.chat.chat_completion_content_part_image_param import ImageURL
from openai_client import (
    create_client,
)
from openai_client.tokens import num_tokens_from_messages, num_tokens_from_tools_and_messages
from semantic_workbench_api_model import workbench_model
from semantic_workbench_api_model.workbench_model import (
    ConversationMessage,
    ConversationParticipant,
    MessageType,
    NewConversationMessage,
    UpdateParticipant,
)
from semantic_workbench_assistant.assistant_app import (
    ConversationContext,
)

from assistant.config import AssistantConfigModel
from assistant.filesystem import (
    EDIT_TOOL_DESCRIPTION_HOSTED,
    EDIT_TOOL_DESCRIPTION_LOCAL,
    VIEW_TOOL_OBJ,
    AttachmentsExtension,
)
from assistant.filesystem._prompts import FILES_PROMPT
from assistant.guidance.dynamic_ui_inspector import get_dynamic_ui_state, update_dynamic_ui_state
from assistant.guidance.guidance_prompts import DYNAMIC_UI_TOOL_NAME, DYNAMIC_UI_TOOL_OBJ
from assistant.response.completion_handler import handle_completion
from assistant.response.models import StepResult
from assistant.response.utils import get_ai_client_configs, get_completion, get_openai_tools_from_mcp_sessions
from assistant.response.utils.formatting_utils import format_message
from assistant.response.utils.message_utils import (
    conversation_message_to_assistant_message,
    conversation_message_to_tool_message,
    conversation_message_to_user_message,
)
from assistant.response.utils.tokens_tiktoken import TokenizerOpenAI
from assistant.whiteboard import notify_whiteboard

logger = logging.getLogger(__name__)

# region Initialization


class ConversationResponder:
    def __init__(
        self,
        message: ConversationMessage,
        context: ConversationContext,
        config: AssistantConfigModel,
        metadata: dict[str, Any],
        attachments_extension: AttachmentsExtension,
    ) -> None:
        self.message = message
        self.context = context
        self.config = config
        self.metadata = metadata
        self.attachments_extension = attachments_extension

        self.stack = AsyncExitStack()

        # Constants
        self.token_model = "gpt-4o"
        self.max_system_prompt_component_tokens = 2000
        # Max number of tokens that should go into a request
        self.max_total_tokens = int(self.config.generative_ai_client_config.request_config.max_tokens * 0.95)
        # If max_token_tokens is exceeded, applying context management should get back under self.max_total_tokens - self.token_buffer
        self.token_buffer = int(self.config.generative_ai_client_config.request_config.response_tokens * 1.1)

        self.tokenizer = TokenizerOpenAI(model=self.token_model)

    @classmethod
    async def create(
        cls,
        message: ConversationMessage,
        context: ConversationContext,
        config: AssistantConfigModel,
        metadata: dict[str, Any],
        attachments_extension: AttachmentsExtension,
    ) -> "ConversationResponder":
        responder = cls(message, context, config, metadata, attachments_extension)
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
            self.sampling_handler,
            step_result,
            completion,
            self.mcp_sessions,
            self.context,
            self.config.generative_ai_client_config.request_config,
            "SILENCE",  # TODO: This is not being used correctly.
            f"respond_to_conversation:step_{step_count}",
            response_start_time,
            self.attachments_extension,
            self.config.orchestration.guidance.enabled,
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
        # Remove any view tool that was added by an MCP server and replace it with ours
        tools = [tool for tool in tools if tool["function"]["name"] != "view"]
        tools.append(VIEW_TOOL_OBJ)
        # Override the description of the edit_file depending on the environment
        tools = self._override_edit_file_description(tools)

        # Start constructing main system prompt
        main_system_prompt = self.config.orchestration.prompts.orchestration_prompt
        # Inject the {{knowledge_cutoff}} and {{current_date}} placeholders
        main_system_prompt = render(
            main_system_prompt,
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
                await self._construct_dynamic_ui_system_prompt(), self.max_system_prompt_component_tokens
            )
            main_system_prompt += "\n\n" + dynamic_ui_system_prompt.strip()

        # Filesystem System Prompt
        filesystem_system_prompt = self.tokenizer.truncate_str(
            await self._construct_filesystem_system_prompt(), self.max_system_prompt_component_tokens
        )
        main_system_prompt += "\n\n" + filesystem_system_prompt.strip()

        # Add specific guidance from MCP servers
        mcp_prompts = await get_mcp_server_prompts(self.mcp_sessions)
        mcp_prompt_string = self.tokenizer.truncate_str(
            "## MCP Servers" + "\n\n" + "\n\n".join(mcp_prompts), self.max_system_prompt_component_tokens
        )
        main_system_prompt += "\n\n" + mcp_prompt_string.strip()

        # Always append the guardrails postfix at the end.
        main_system_prompt += "\n\n" + self.config.orchestration.prompts.guardrails_prompt.strip()

        logging.info("The system prompt has been constructed.")

        main_system_prompt = ChatCompletionSystemMessageParam(
            role="system",
            content=main_system_prompt,
        )

        chat_history = await self._construct_oai_chat_history()
        chat_history = await self._check_token_budget([main_system_prompt, *chat_history], tools)
        return tools, chat_history

    async def _construct_oai_chat_history(self) -> list[ChatCompletionMessageParam]:
        participants_response = await self.context.get_participants(include_inactive=True)
        participants = participants_response.participants
        history = []
        before_message_id = None
        while True:
            messages_response = await self.context.get_messages(
                limit=100, before=before_message_id, message_types=[MessageType.chat, MessageType.note, MessageType.log]
            )
            messages_list = messages_response.messages
            for message in messages_list:
                history.extend(await self._conversation_message_to_chat_message_params(message, participants))

            if not messages_list or messages_list.count == 0:
                break

            before_message_id = messages_list[0].id

        # TODO: Re-order tool call messages if there is an interruption between the tool call and its response.

        logger.info(f"Chat history has been constructed with {len(history)} messages.")
        return history

    async def _conversation_message_to_chat_message_params(
        self,
        message: ConversationMessage,
        participants: list[ConversationParticipant],
    ) -> list[ChatCompletionMessageParam]:
        # some messages may have multiple parts, such as a text message with an attachment
        chat_message_params: list[ChatCompletionMessageParam] = []

        # add the message to list, treating messages from a source other than this assistant as a user message
        if message.message_type == MessageType.note:
            # we are stuffing tool messages into the note message type, so we need to check for that
            tool_message = conversation_message_to_tool_message(message)
            if tool_message is not None:
                chat_message_params.append(tool_message)
            else:
                logger.warning(f"Failed to convert tool message to completion message: {message}")

        elif message.message_type == MessageType.log:
            # Assume log messages are dynamic ui choice messages which are treated as user messages
            user_message = conversation_message_to_user_message(message, participants)
            chat_message_params.append(user_message)

        elif message.sender.participant_id == self.context.assistant.id:
            # add the assistant message to the completion messages
            assistant_message = conversation_message_to_assistant_message(message, participants)
            chat_message_params.append(assistant_message)

        else:
            # add the user message to the completion messages
            user_message_text = format_message(message, participants)
            # Iterate over the attachments associated with this message and append them at the end of the message.
            image_contents = []
            for filename in message.filenames:
                attachment_content = await self.attachments_extension.get_attachment(self.context, filename)
                if attachment_content:
                    if attachment_content.startswith("data:image/"):
                        image_contents.append(
                            ChatCompletionContentPartImageParam(
                                type="image_url",
                                image_url=ImageURL(url=attachment_content, detail="high"),
                            )
                        )
                    else:
                        user_message_text += f"\n\n<file filename={filename}>\n{attachment_content}</file>"

            if image_contents:
                chat_message_params.append(
                    ChatCompletionUserMessageParam(
                        role="user",
                        content=[
                            ChatCompletionContentPartTextParam(
                                type="text",
                                text=user_message_text,
                            )
                        ]
                        + image_contents,
                    )
                )
            else:
                chat_message_params.append(
                    ChatCompletionUserMessageParam(
                        role="user",
                        content=user_message_text,
                    )
                )
        return chat_message_params

    async def _construct_dynamic_ui_system_prompt(self) -> str:
        current_dynamic_ui_elements = await get_dynamic_ui_state(context=self.context)

        if not current_dynamic_ui_elements:
            current_dynamic_ui_elements = "No dynamic UI elements have been generated yet. Consider generating some."

        system_prompt = "## On Dynamic UI Elements\n"
        system_prompt += "\n" + self.config.orchestration.guidance.prompt
        system_prompt += "\n" + str(current_dynamic_ui_elements)
        return system_prompt

    async def _construct_filesystem_system_prompt(self) -> str:
        """
        Constructs the files available to the assistant with the following format:
        ##  Files
        - path.pdf (r--) - [topics][summary]
        - path.md (rw-) - [topics][summary]
        """
        attachment_filenames = await self.attachments_extension.get_attachment_filenames(self.context)
        doc_editor_filenames = await self.attachments_extension._inspectors.list_document_filenames(self.context)

        all_files = [(filename, "-r--") for filename in attachment_filenames]
        all_files.extend([(filename, "-rw-") for filename in doc_editor_filenames])
        all_files.sort(key=lambda x: x[0])

        system_prompt = f"{FILES_PROMPT}" + "\n\n### Files\n"
        if not all_files:
            system_prompt += "\nNo files have been added or created yet."
        else:
            system_prompt += "\n".join([f"- {filename} ({permission})" for filename, permission in all_files])
        return system_prompt

    async def _check_token_budget(
        self, messages: list[ChatCompletionMessageParam], tools: list[ChatCompletionToolParam]
    ) -> list[ChatCompletionMessageParam]:
        """
        Checks if the token budget is exceeded. If it is, it will call the context management function to remove messages.
        """
        current_tokens = num_tokens_from_tools_and_messages(tools, messages, self.token_model)
        if current_tokens > self.max_total_tokens:
            logger.info(
                f"Token budget exceeded: {current_tokens} > {self.max_total_tokens}. Applying context management."
            )
            messages = await self._context_management(messages, tools)
            return messages
        else:
            return messages

    async def _context_management(
        self, messages: list[ChatCompletionMessageParam], tools: list[ChatCompletionToolParam]
    ) -> list[ChatCompletionMessageParam]:
        """
        Returns a list of messages that has been modified to fit within the token budget.
        The algorithm implemented here will:
        - Always include the system prompt, the first two messages afterward, and the tools.
        - Then start removing messages until the token count is under the max_tokens - token_buffer.
        - Care needs to be taken to not remove a tool call, while leaving the corresponding assistant tool call.
        """
        target_token_count = self.max_total_tokens - self.token_buffer

        # Always keep the system message and the first message after (this is the welcome msg)
        # Also keep the last two messages. Assumes these will not give us an overage for now.
        initial_messages = messages[0:2]
        recent_messages = messages[-2:] if len(messages) >= 4 else messages[3:]
        current_tokens = num_tokens_from_tools_and_messages(tools, initial_messages + recent_messages, self.token_model)

        middle_messages = messages[2:-2] if len(messages) >= 4 else []

        filtered_middle_messages = []
        if current_tokens <= target_token_count and middle_messages:
            length = len(middle_messages)
            i = length - 1
            while i >= 0:
                # If tool role, go back and get the corresponding assistant message and check the tokens together.
                # If the message(s) would go over the limit, don't add them and terminate the loop.
                if middle_messages[i]["role"] == "tool":
                    # Check to see if the previous message is an assistant message with the same tool call id.
                    # Parallel tool calling is off, so assume the previous message is the assistant message and error otherwise.
                    if (
                        i <= 0
                        or middle_messages[i - 1]["role"] != "assistant"
                        or middle_messages[i - 1]["tool_calls"][0]["id"] != middle_messages[i]["tool_call_id"]  # type: ignore
                    ):
                        logger.error(
                            f"Tool message {middle_messages[i]} does not have a corresponding assistant message."
                        )
                        raise ValueError(
                            f"Tool message {middle_messages[i]} does not have a corresponding assistant message."
                        )

                    # Get the assistant message and check the tokens together.
                    msgs = [middle_messages[i], middle_messages[i - 1]]
                    i -= 1
                else:
                    msgs = [middle_messages[i]]

                msgs_tokens = num_tokens_from_messages(msgs, self.token_model)
                if current_tokens + msgs_tokens <= target_token_count:
                    filtered_middle_messages.extend(msgs)
                    current_tokens += msgs_tokens
                else:
                    break
                i -= 1

        initial_messages.extend(reversed(filtered_middle_messages))
        preserved_messages = initial_messages + recent_messages
        return preserved_messages

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
        except Exception as e:
            logger.error(f"Failed to override edit_file description: {e}")
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
