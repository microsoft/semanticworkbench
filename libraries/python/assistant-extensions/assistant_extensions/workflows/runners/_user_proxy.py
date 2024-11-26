import asyncio
import traceback
from contextlib import asynccontextmanager, suppress
from dataclasses import dataclass
from typing import TYPE_CHECKING, Any, AsyncGenerator, Awaitable, Callable

from semantic_workbench_api_model.workbench_model import (
    ConversationMessage,
    MessageSender,
    MessageType,
    NewConversation,
    NewConversationMessage,
    UpdateParticipant,
)
from semantic_workbench_assistant.assistant_app import AssistantContext, ConversationContext

from .._model import UserProxyWorkflowDefinition, WorkflowsConfigModel

if TYPE_CHECKING:
    from .._workflows import WorkflowsProcessingErrorHandler


@dataclass
class WorkflowState:
    id: str
    context: ConversationContext
    definition: UserProxyWorkflowDefinition
    send_as: MessageSender
    current_step: int
    metadata: dict[str, Any]


@asynccontextmanager
async def send_error_message_on_exception(context: ConversationContext) -> AsyncGenerator[None, None]:
    try:
        yield
    except Exception as e:
        await context.send_messages(
            NewConversationMessage(
                content=f"An error occurred: {e}",
                message_type=MessageType.notice,
                metadata={
                    "debug": {"stack_trace": traceback.format_exc()},
                    "attribution": "workflows",
                },
            )
        )


class UserProxyRunner:
    def __init__(
        self,
        config_provider: Callable[[AssistantContext], Awaitable[WorkflowsConfigModel]],
        error_handler: "WorkflowsProcessingErrorHandler",
    ) -> None:
        """
        User Proxy General flow:
        - User builds context within the conversation until ready to execute a workflow.
        - User triggers the workflow by sending a command.
        - The extension receives the command and starts the workflow process.
            - Inform the user that the workflow has started.
            - Duplicate the conversation (with files and assistants) for the workflow.
            - Update status to indicate the workflow is on step #1.
            - Create a new message on the new conversation, taken from step #1 of the workflow definition.
            - Wait for assistant to respond.
            - Repeat until workflow is complete, updating status on each step.
            - Create a new message on the original conversation using the final assistant response as content.
            - Disconnect the workflow conversation.

        Example workflow definition:
        - Workflow name: "Ensure document is rooted in ground truth"
        - Assumes: "User has created enough context in the conversation to determine if a document is rooted in
            ground truth. This may be because they co-created a document with an assistant from other artifacts
            such as meeting transcripts and technical notes, or similar."
        - Steps: (overly simplified for example, much higher quality prompts will likely get much better results)
          1. "Evaluate the document to determine if it is rooted in ground truth using DMAIC (Define, Measure,
            Analyze, Improve, Control). Please ...more instruction here..."
          2. "Considering these results, what are the specific edits needed to ensure the document is rooted in
            ground truth? Make discreet lists of additions, edits, and removals and include locations ... more"
          3. "Provide the detailed list and a very user-friendly explanation of the rationale for a non-technical
            audience."
        """
        self.config_provider = config_provider
        self.error_handler = error_handler
        self._workflow_complete_event = asyncio.Event()

    async def run(
        self,
        context: ConversationContext,
        workflow_definition: UserProxyWorkflowDefinition,
        send_as: MessageSender,
        metadata: dict[str, Any] = {},
    ) -> None:
        """
        Run the user proxy runner.
        """
        # inform the user that the workflow has started and get going!
        async with send_error_message_on_exception(context):
            # context.set_status(f"Starting workflow: {workflow_definition.name}")
            await context.update_participant_me(
                UpdateParticipant(status=f"Starting workflow: {workflow_definition.name}")
            )

            # duplicate the current conversation and get the context
            workflow_context = await self.duplicate_conversation(context, workflow_definition)

            # set the current workflow id
            workflow_state = WorkflowState(
                id=workflow_context.id,
                context=workflow_context,
                definition=workflow_definition,
                send_as=send_as,
                current_step=1,
                metadata=metadata,
            )
            self.current_workflow_state = workflow_state

            event_listener_task = asyncio.create_task(
                self._listen_for_events(context, workflow_state, workflow_context.id)
            )

            try:
                # start the workflow
                await self._start_step(context, workflow_state)

                # wait for the workflow to complete
                await self._workflow_complete_event.wait()
            except Exception as e:
                await self.error_handler(context, workflow_state.definition.command, e)
            finally:
                event_listener_task.cancel()
                with suppress(asyncio.CancelledError):
                    await event_listener_task

    async def _listen_for_events(
        self, context: ConversationContext, workflow_state: WorkflowState, event_source_url: str
    ) -> None:
        """
        Listen for events.
        """

        # set up the event source for the workflow
        events_base_url = context._workbench_client._client._base_url
        events_path = f"conversations/{workflow_state.context.id}/events"
        event_source_url = f"{events_base_url}{events_path}"

        async for sse_event in context._workbench_client.get_sse_session(event_source_url):
            if (
                sse_event["event"] == "message.created"
                and sse_event["data"] is not None
                and sse_event["data"]["data"] is not None
                and sse_event["data"]["data"]["message"] is not None
            ):
                message_data = sse_event["data"]["data"]["message"]
                message = ConversationMessage.model_validate(message_data)
                if message.sender and message.sender.participant_role != "assistant":
                    continue
                await self._on_assistant_message(context, workflow_state, message)

    async def duplicate_conversation(
        self, context: ConversationContext, workflow_definition: UserProxyWorkflowDefinition
    ) -> ConversationContext:
        """
        Duplicate the current conversation
        """

        title = f"Workflow: {workflow_definition.name} [{context.title}]"

        # duplicate the current conversation
        response = await context._workbench_client.duplicate_conversation(
            new_conversation=NewConversation(
                title=title,
                metadata={"parent_conversation_id": context.id},
            )
        )

        conversation_id = response.conversation_ids[0]

        # create a new conversation context
        workflow_context = ConversationContext(
            id=str(conversation_id),
            title=title,
            assistant=context.assistant,
        )

        # send link to chat for the new conversation
        await context.send_messages(
            NewConversationMessage(
                content=f"New conversation: {title}",
                message_type=MessageType.command_response,
                metadata={"attribution": "workflows:user_proxy", "href": f"/{conversation_id}"},
            )
        )

        # return the new conversation context
        return workflow_context

    async def _start_step(self, context: ConversationContext, workflow_state: WorkflowState) -> None:
        """
        Start a step in the workflow.
        """

        # update status to indicate the workflow is on step #<current step>
        # context.set_status(f"Workflow {workflow_state.definition.name}: Step {workflow_state.current_step}")

        # create a new message on the new conversation, taken from the current step of the workflow definition
        user_message = workflow_state.definition.user_messages[workflow_state.current_step - 1]
        await workflow_state.context.send_messages(
            NewConversationMessage(
                sender=workflow_state.send_as,
                content=user_message.message,
                message_type=MessageType.chat,
                metadata={"attribution": "user"},
            )
        )

        # update status to indicate the workflow is awaiting the assistant response
        # context.set_status(
        #     f"Workflow {workflow_state.definition.name}: Step {workflow_state.current_step}, awaiting assistant response..."
        # )
        await context.update_participant_me(
            UpdateParticipant(
                status=f"Workflow {workflow_state.definition.name} [Step {workflow_state.current_step} - {user_message.status_label}]: awaiting assistant response..."
            )
        )

    async def _on_assistant_message(
        self,
        context: ConversationContext,
        workflow_state: WorkflowState,
        assistant_response: ConversationMessage,
    ) -> None:
        """
        Handle the assistant response.
        """

        if self.current_workflow_state is None:
            # not sure how we got here, but let's just ignore it
            return

        # verify we're still in the same run
        if self.current_workflow_state.context.id != workflow_state.context.id:
            # abort and cleanup
            await self._cleanup(context, workflow_state)
            return

        # determine if there are more steps
        if workflow_state.current_step < len(workflow_state.definition.user_messages):
            # increment the current step
            workflow_state.current_step += 1

            # start the next step
            await self._start_step(context, workflow_state)
        else:
            # send the final response
            await self._send_final_response(context, workflow_state, assistant_response)

            # cleanup
            await self._cleanup(context, workflow_state)

            # Signal workflow completion
            self._workflow_complete_event.set()

    async def _send_final_response(
        self, context: ConversationContext, workflow_state: WorkflowState, assistant_response: ConversationMessage
    ) -> None:
        """
        Send the final response to the user.
        """

        # update status to indicate the workflow is complete
        # context.set_status(f"Workflow {workflow_state.definition.name}: retrieving final response...")
        # await context.update_participant_me(
        #     UpdateParticipant(status=f"Workflow {workflow_state.definition.name}: retrieving final response...")
        # )

        # create a new message on the original conversation using the final assistant response as content
        await context.send_messages(
            NewConversationMessage(
                content=assistant_response.content,
                message_type=MessageType.chat,
                metadata={"attribution": "workflows:user_proxy"},
            )
        )

    async def _cleanup(self, context: ConversationContext, workflow_state: WorkflowState) -> None:
        """
        Disconnect the workflow conversation.
        """

        # clear the status
        await context.update_participant_me(UpdateParticipant(status=None))

        # disconnect the workflow conversation
        await context._workbench_client.delete_conversation()
        self.current_workflow_state = None
