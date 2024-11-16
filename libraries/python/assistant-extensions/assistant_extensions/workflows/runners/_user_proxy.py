import json
import traceback
from contextlib import asynccontextmanager
from dataclasses import dataclass
from typing import TYPE_CHECKING, AsyncGenerator, Awaitable, Callable

import aiohttp
from semantic_workbench_api_model.workbench_model import (
    ConversationMessage,
    MessageType,
    NewConversationMessage,
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
    current_step: int


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

    async def run(
        self, context: ConversationContext, workflow_definition: UserProxyWorkflowDefinition, user_id: str
    ) -> None:
        """
        Run the user proxy runner.
        """
        # inform the user that the workflow has started and get going!
        async with send_error_message_on_exception(context), context.set_status(
            f"Workflow {workflow_definition.name}: Starting..."
        ):
            # duplicate the current conversation and get the context
            workflow_context = await self.duplicate_conversation(context, user_id)

            # set the current workflow id
            workflow_state = WorkflowState(
                id=workflow_context.id,
                context=context,
                definition=workflow_definition,
                current_step=1,
            )
            self.current_workflow_state = workflow_state

            # set up the event source for the workflow
            events_base_url = context._workbench_client._client._base_url
            events_path = f"/conversations/{workflow_context.id}/events"
            event_source_url = f"{events_base_url}{events_path}"
            async with aiohttp.ClientSession() as session:
                async with session.get(event_source_url) as response:
                    async for line in response.content:
                        # Process the SSE events
                        if line:
                            event_data = line.decode("utf-8").strip()
                            if event_data.startswith("data:"):
                                json_data = event_data[5:].strip()
                                event = json.loads(json_data)
                                if event["type"] == "message_created" and event["data"] is not None:
                                    assistant_response = ConversationMessage.model_validate(event["data"])
                                    await self._on_assistant_message(context, workflow_state, assistant_response)

            # start the workflow
            await self._start_step(context, workflow_state)

    async def duplicate_conversation(self, context: ConversationContext, user_id: str) -> ConversationContext:
        """
        Duplicate the current conversation
        """

        # duplicate the current conversation
        response = await context._workbench_client.duplicate_conversation(user_id)

        # create a new conversation context
        workflow_context = ConversationContext(
            id=str(response.conversation_ids[0]),
            title="Workflow",
            assistant=context.assistant,
        )

        # return the new conversation context
        return workflow_context

    async def _start_step(self, context: ConversationContext, workflow_state: WorkflowState) -> None:
        """
        Start a step in the workflow.
        """

        # update status to indicate the workflow is on step #<current step>
        context.set_status(
            f"Workflow {workflow_state.definition.name}: Step {workflow_state.current_step}, sending user message..."
        )

        # create a new message on the new conversation, taken from the current step of the workflow definition
        user_message = workflow_state.definition.user_messages[workflow_state.current_step - 1]
        await workflow_state.context.send_messages(
            NewConversationMessage(
                content=user_message,
                message_type=MessageType.chat,
                metadata={"attribution": "user"},
            )
        )

        # update status to indicate the workflow is awaiting the assistant response
        context.set_status(
            f"Workflow {workflow_state.definition.name}: Step {workflow_state.current_step}, awaiting assistant response..."
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
            await self._send_final_response(context, assistant_response)

            # cleanup
            await self._cleanup(context, workflow_state)

    async def _send_final_response(self, context: ConversationContext, assistant_response: ConversationMessage) -> None:
        """
        Send the final response to the user.
        """

        # create a new message on the original conversation using the final assistant response as content
        await context.send_messages(
            NewConversationMessage(
                content=assistant_response.content,
                message_type=MessageType.chat,
                metadata={"attribution": "system"},
            )
        )

    async def _cleanup(self, context: ConversationContext, workflow_state: WorkflowState) -> None:
        """
        Disconnect the workflow conversation.
        """

        # disconnect the workflow conversation
        await context._workbench_client.delete_conversation()
        self.current_workflow_state = None
