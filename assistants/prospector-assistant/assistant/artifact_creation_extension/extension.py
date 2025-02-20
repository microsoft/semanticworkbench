import logging
from textwrap import dedent

import openai_client
from openai.types.chat import (
    ChatCompletionAssistantMessageParam,
    ChatCompletionDeveloperMessageParam,
    ChatCompletionMessageParam,
    ChatCompletionUserMessageParam,
)
from semantic_workbench_api_model.workbench_model import (
    ConversationEvent,
    ConversationMessage,
    MessageType,
    NewConversationMessage,
    ParticipantRole,
)
from semantic_workbench_assistant.assistant_app.config import BaseModelAssistantConfig
from semantic_workbench_assistant.assistant_app.context import ConversationContext
from semantic_workbench_assistant.assistant_app.protocol import AssistantAppProtocol

from ..config import AssistantConfigModel
from . import store, tools
from ._llm import CompletionTool, MessageResponse, ToolCallResponse, completion_with_tools
from .config import LLMConfig
from .store import ActiveDocumentInspector, DocumentWorkspaceInspector

logger = logging.getLogger(__name__)


system_message = dedent(
    """
    You are an assistant. Ultimately, you help users create documents in a document workspace. To do this, you
    will assist with ideation, drafting, and editing. Documents are can represent a variety of content types,
    such as reports, articles, blog posts, stories, slide decks or others. You can create, update, and remove
    documents, as well as create, update, and remove sections within documents. You can also list all documents
    in the workspace.
    The documents in the workspace, in their current state, are available here for your reference.

    Documents:
    ---
    """
)


class ArtifactCreationExtension:
    def __init__(
        self, assistant_app: AssistantAppProtocol, assistant_config: BaseModelAssistantConfig[AssistantConfigModel]
    ) -> None:
        document_workspace_inspector = DocumentWorkspaceInspector()
        active_document_inspector = ActiveDocumentInspector()
        assistant_app.add_inspector_state_provider(
            document_workspace_inspector.display_name, document_workspace_inspector
        )
        assistant_app.add_inspector_state_provider(active_document_inspector.display_name, active_document_inspector)

        @assistant_app.events.conversation.message.command.on_created
        async def on_message_command_created(
            context: ConversationContext, _: ConversationEvent, message: ConversationMessage
        ) -> None:
            config = await assistant_config.get(context.assistant)
            if config.guided_workflow != "Long Document Creation":
                return

            match message.content.split(" ")[0]:
                case "/help":
                    await _send_message(
                        context,
                        dedent("""
                        /help - Display this help message.
                        /ls - List all documents in the workspace.
                        /select <number> - Select the active document.
                        """),
                        {},
                        message_type=MessageType.command_response,
                    )

                case "/ls":
                    args = tools.ListDocumentsArgs()
                    args.set_context(context)
                    headers = await tools.list_documents(args)
                    document_list = "\n".join(
                        f"{index}. {header.title} ({header.document_id})"
                        for index, header in enumerate(headers.documents)
                    )
                    await _send_message(
                        context,
                        f"Documents in the workspace: {headers.count}\n\n{document_list}",
                        {},
                        message_type=MessageType.command_response,
                    )

                case "/select":
                    index = int(message.content.split(" ")[1])
                    list_args = tools.ListDocumentsArgs()
                    list_args.set_context(context)
                    headers = await tools.list_documents(list_args)
                    store.active_document_id = headers.documents[index].document_id
                    await _send_message(
                        context,
                        f"Selected document: {headers.documents[index].title}",
                        {},
                        message_type=MessageType.command_response,
                    )

                case _:
                    await _send_message(
                        context,
                        "Unknown command. Use /help to see available commands.",
                        {},
                        message_type=MessageType.command_response,
                    )

        @assistant_app.events.conversation.message.chat.on_created
        async def on_message_chat_created(
            context: ConversationContext, _: ConversationEvent, message: ConversationMessage
        ) -> None:
            config = await assistant_config.get(context.assistant)
            if config.guided_workflow != "Long Document Creation":
                return

            async with context.set_status("responding ..."):
                messages_response = await context.get_messages(before=message.id)

                async def message_generator() -> list[ChatCompletionMessageParam]:
                    messages: list[ChatCompletionMessageParam] = []
                    for msg in (*messages_response.messages, message):
                        match msg.sender.participant_role:
                            case ParticipantRole.user:
                                messages.append(ChatCompletionUserMessageParam(content=msg.content, role="user"))

                            case ParticipantRole.assistant:
                                messages.append(
                                    ChatCompletionAssistantMessageParam(content=msg.content, role="assistant")
                                )

                    list_args = tools.ListDocumentsArgs()
                    list_args.set_context(context)
                    headers = await tools.list_documents(list_args)
                    document_content_list = ""
                    if not headers:
                        document_content_list = "There are currently documents in the workspace."

                    for header in headers.documents:
                        get_document_args = tools.GetDocumentArgs(document_id=header.document_id)
                        get_document_args.set_context(context)
                        document = await tools.get_document(get_document_args)

                        document_content_list += f"\n\n```json\n{document.model_dump_json()}\n```"

                    messages.append(
                        # ChatCompletionSystemMessageParam(content=system_message + document_content_list, role="system")
                        ChatCompletionDeveloperMessageParam(
                            content=system_message + document_content_list, role="developer"
                        )
                    )
                    return messages

                completion_tools = [
                    CompletionTool(
                        function=tools.create_document,
                        argument_model=tools.CreateDocumentArgs,
                    ),
                    CompletionTool(
                        function=tools.update_document,
                        argument_model=tools.UpdateDocumentArgs,
                    ),
                    CompletionTool(
                        function=tools.remove_document,
                        argument_model=tools.RemoveDocumentArgs,
                    ),
                    CompletionTool(
                        function=tools.get_document,
                        argument_model=tools.GetDocumentArgs,
                    ),
                    CompletionTool(
                        function=tools.create_document_section,
                        argument_model=tools.CreateDocumentSectionArgs,
                    ),
                    CompletionTool(
                        function=tools.update_document_section,
                        argument_model=tools.UpdateDocumentSectionArgs,
                    ),
                    CompletionTool(
                        function=tools.remove_document_section,
                        argument_model=tools.RemoveDocumentSectionArgs,
                    ),
                    CompletionTool(
                        function=tools.list_documents,
                        argument_model=tools.ListDocumentsArgs,
                    ),
                ]

                config = await assistant_config.get(context.assistant)
                config.service_config.azure_openai_deployment = "o3-mini"  # type: ignore
                llm_config = LLMConfig(
                    openai_client_factory=lambda: openai_client.create_client(config.service_config),
                    openai_model="o3-mini",  # config.request_config.openai_model,
                    max_response_tokens=config.request_config.response_tokens,
                )

                try:
                    async for response in completion_with_tools(
                        llm_config=llm_config,
                        context=context,
                        get_messages=lambda: message_generator(),
                        tools=completion_tools,
                    ):
                        match response:
                            case MessageResponse():
                                await _send_message(context, response.message, response.metadata)

                            case ToolCallResponse():
                                async with (
                                    context.state_updated_event_after(document_workspace_inspector.display_name),
                                    context.state_updated_event_after(active_document_inspector.display_name),
                                ):
                                    await _send_message(
                                        context,
                                        f"Called {response.tool_call.function.name}",
                                        response.metadata,
                                        message_type=MessageType.notice,
                                    )

                except Exception as e:
                    logger.exception("Failed to generate completion.")
                    await _send_error_message(context, "Failed to generate completion.", {"error": str(e)})
                    return


async def _send_message(
    context: ConversationContext, message: str, debug: dict, message_type: MessageType = MessageType.chat
) -> None:
    if not message:
        return

    await context.send_messages(
        NewConversationMessage(
            content=message,
            message_type=message_type,
            debug_data=debug,
        )
    )


async def _send_error_message(context: ConversationContext, message: str, debug: dict) -> None:
    await context.send_messages(
        NewConversationMessage(
            content=message,
            message_type=MessageType.notice,
            debug_data=debug,
        )
    )
