import logging
from typing import Any, Awaitable, Callable

import deepmerge
from semantic_workbench_api_model.workbench_model import (
    ConversationEvent,
    ConversationMessage,
    MessageType,
    NewConversationMessage,
)
from semantic_workbench_assistant.assistant_app import AssistantAppProtocol, AssistantContext, ConversationContext

from assistant_extensions.workflows.runners._user_proxy import UserProxyRunner

from ._model import WorkflowsConfigModel

logger = logging.getLogger(__name__)

WorkflowsProcessingErrorHandler = Callable[[ConversationContext, str, Exception], Awaitable]


trigger_command = "workflow"


async def log_and_send_message_on_error(context: ConversationContext, filename: str, e: Exception) -> None:
    """
    Default error handler for attachment processing, which logs the exception and sends
    a message to the conversation.
    """

    logger.exception("exception occurred processing attachment", exc_info=e)
    await context.send_messages(
        NewConversationMessage(
            content=f"There was an error processing the attachment ({filename}): {e}",
            message_type=MessageType.notice,
            metadata={"attribution": "workflows"},
        )
    )


class WorkflowsExtension:
    def __init__(
        self,
        assistant: AssistantAppProtocol,
        content_safety_metadata_key: str,
        config_provider: Callable[[AssistantContext], Awaitable[WorkflowsConfigModel]],
        error_handler: WorkflowsProcessingErrorHandler = log_and_send_message_on_error,
    ) -> None:
        """
        WorkflowsExtension enables the assistant to execute pre-configured workflows. Current workflows act
        as an auto-proxy for a series of user messages. Future workflows may include more complex interactions.
        """

        self._error_handler = error_handler
        self._user_proxy_runner = UserProxyRunner(config_provider, error_handler)

        @assistant.events.conversation.message.command.on_created
        async def on_command_message_created(
            context: ConversationContext, event: ConversationEvent, message: ConversationMessage
        ) -> None:
            config = await config_provider(context.assistant)
            metadata: dict[str, Any] = {"debug": {"content_safety": event.data.get(content_safety_metadata_key, {})}}

            if not config.enabled or message.command_name != f"/{trigger_command}":
                return

            if len(message.command_args) > 0:
                await self.on_command(config, context, message, metadata)
            else:
                await self.on_help(config, context, metadata)

    async def on_help(
        self,
        config: WorkflowsConfigModel,
        context: ConversationContext,
        metadata: dict[str, Any] = {},
    ) -> None:
        # Iterate over the workflow definitions and create a list of commands in markdown format
        content = "Available workflows:\n"
        for workflow in config.workflow_definitions:
            content += f"- `{workflow.command}`: {workflow.description}\n"

        # send the message
        await context.send_messages(
            NewConversationMessage(
                content=content,
                message_type=MessageType.command_response,
                metadata=deepmerge.always_merger.merge(
                    metadata,
                    {"attribution": "workflows"},
                ),
            )
        )

    async def on_command(
        self,
        config: WorkflowsConfigModel,
        context: ConversationContext,
        message: ConversationMessage,
        metadata: dict[str, Any] = {},
    ) -> None:
        # find the workflow definition
        workflow_command = message.command_args.split(" ")[0]
        workflow_definition = None
        for workflow in config.workflow_definitions:
            if workflow.command == workflow_command:
                workflow_definition = workflow
                break

        if workflow_definition is None:
            await self.on_help(config, context, metadata)
            return

        # run the user proxy runner
        await self._user_proxy_runner.run(context, workflow_definition, message.sender)
