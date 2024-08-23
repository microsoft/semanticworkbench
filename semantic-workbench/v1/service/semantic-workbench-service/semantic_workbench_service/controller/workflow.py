import uuid
from typing import Any, AsyncContextManager, Callable, Tuple

import openai.types.chat
from azure.identity.aio import DefaultAzureCredential, get_bearer_token_provider
from openai import AsyncAzureOpenAI
from semantic_workbench_api_model.assistant_model import ConfigPutRequestModel
from semantic_workbench_api_model.workbench_model import (
    AssistantList,
    Conversation,
    ConversationMessage,
    MessageType,
    NewAssistant,
    NewConversation,
    NewConversationMessage,
    NewWorkflowDefinition,
    NewWorkflowRun,
    ParticipantRole,
    UpdateAssistant,
    UpdateConversation,
    UpdateParticipant,
    UpdateWorkflowDefinition,
    UpdateWorkflowParticipant,
    UpdateWorkflowRun,
    UpdateWorkflowRunMappings,
    WorkflowAssistantMapping,
    WorkflowConversationMapping,
    WorkflowDefinition,
    WorkflowDefinitionList,
    WorkflowParticipant,
    WorkflowRun,
    WorkflowRunList,
    WorkflowTransition,
)
from sqlmodel import select
from sqlmodel.ext.asyncio.session import AsyncSession

from .. import auth, db, query, service_user_principals, settings
from . import AssistantController, ConversationController, convert, exceptions
from . import user as user_
from .conversation import MessagePreview

default_context_transfer_instruction = (
    "Generate content that can be a note pasted in before the first message in a new conversation"
    " that is made up of different participants with no context of the previous conversation. This"
    " note should not originate from or target any specific participant(s) and should be able to"
    " transfer just the context asked for in the <CONTEXT_TRANSFER_REQUEST/>."
)


class WorkflowController:

    def __init__(
        self,
        get_session: Callable[[], AsyncContextManager[AsyncSession]],
        assistant_controller: AssistantController,
        conversation_controller: ConversationController,
    ) -> None:
        self._get_session = get_session
        self._assistant_controller = assistant_controller
        self._conversation_controller = conversation_controller

    #
    # Public methods
    #

    async def preview_message(self, message_preview: MessagePreview) -> None:

        if (
            # ignore non-chat messages
            message_preview.message.message_type != MessageType.chat
            # ignore messages from the workflow itself
            or message_preview.message.sender.participant_id == service_user_principals.workflow.user_id
        ):
            return

        # get workflow run id for conversation
        workflow_run_id = await self.get_workflow_run_id_for_conversation(
            conversation_id=message_preview.conversation_id,
        )

        if workflow_run_id is None:
            # no workflow run found for conversation
            return

        # indicate that the message is being evaluated
        try:
            try:
                await self._conversation_controller.add_or_update_conversation_participant(
                    conversation_id=message_preview.conversation_id,
                    participant_id=service_user_principals.workflow.user_id,
                    update_participant=UpdateParticipant(
                        status="evaluation in progress...",
                    ),
                    principal=service_user_principals.workflow,
                )
            except Exception as e:
                raise exceptions.RuntimeError(
                    detail=f"failed to update participant status text: {e}",
                ) from e  # indicate that the message is being evaluated

            # evaluate transitions
            try:
                await self.perform_transition_if_applicable(
                    workflow_run_id=uuid.UUID(workflow_run_id),
                )
            except Exception as e:
                raise exceptions.RuntimeError(
                    detail=f"failed to evaluate transitions for conversation: {e}",
                ) from e
        finally:
            # clear participant status text
            try:
                await self._conversation_controller.add_or_update_conversation_participant(
                    conversation_id=message_preview.conversation_id,
                    participant_id=service_user_principals.workflow.user_id,
                    update_participant=UpdateParticipant(status=None),
                    principal=service_user_principals.workflow,
                )
            except Exception as e:
                raise exceptions.RuntimeError(
                    detail=f"failed to clear participant status text: {e}",
                ) from e

    # Workflow Definition

    async def get_workflow_definition(self, workflow_definition_id: uuid.UUID) -> WorkflowDefinition:
        async with self._get_session() as session:
            workflow_definition = (
                await session.exec(
                    query.select(db.WorkflowDefinition).where(
                        db.WorkflowDefinition.workflow_definition_id == workflow_definition_id
                    )
                )
            ).one_or_none()
            if workflow_definition is None:
                raise exceptions.NotFoundError()

        return convert.workflow_definition_from_db(model=workflow_definition)

    async def get_workflow_definitions(
        self, user_principal: auth.UserPrincipal, include_inactive: bool = False
    ) -> WorkflowDefinitionList:
        async with self._get_session() as session:
            workflow_definitions = await session.exec(
                query.select_workflow_definitions_for(user_principal=user_principal, include_inactive=include_inactive)
            )

            return convert.workflow_definition_list_from_db(models=workflow_definitions)

    async def create_workflow_definition(
        self, user_principal: auth.UserPrincipal, new_workflow_definition: NewWorkflowDefinition
    ) -> WorkflowDefinition:
        async with self._get_session() as session:
            await user_.add_or_update_user_from(session=session, user_principal=user_principal)
            workflow_definition = db.WorkflowDefinition(
                data=new_workflow_definition.model_dump(),
            )
            session.add(workflow_definition)
            session.add(
                db.WorkflowUserParticipant(
                    workflow_definition_id=workflow_definition.workflow_definition_id,
                    user_id=user_principal.user_id,
                )
            )
            await session.commit()
            await session.refresh(workflow_definition)

        return convert.workflow_definition_from_db(model=workflow_definition)

    async def update_workflow_definition(
        self,
        user_principal: auth.UserPrincipal,
        workflow_definition_id: uuid.UUID,
        update_workflow_definition: UpdateWorkflowDefinition,
    ) -> WorkflowDefinition:
        async with self._get_session() as session:
            workflow_definition = (
                await session.exec(
                    query.select_workflow_definitions_for(user_principal=user_principal)
                    .where(db.WorkflowDefinition.workflow_definition_id == workflow_definition_id)
                    .with_for_update()
                )
            ).one_or_none()
            if workflow_definition is None:
                raise exceptions.NotFoundError()

            data = workflow_definition.data.copy()
            updates = update_workflow_definition.model_dump(exclude_unset=True, mode="json")
            data.update(updates)
            workflow_definition.data = data

            session.add(workflow_definition)
            await session.commit()
            await session.refresh(workflow_definition)

        return convert.workflow_definition_from_db(model=workflow_definition)

    async def add_or_update_workflow_participant(
        self,
        workflow_definition_id: uuid.UUID,
        participant_id: str,
        update_participant: UpdateWorkflowParticipant,
    ) -> WorkflowParticipant:
        async with self._get_session() as session:
            await db.insert_if_not_exists(
                session,
                db.WorkflowUserParticipant(
                    workflow_definition_id=workflow_definition_id,
                    user_id=participant_id,
                    active_participant=update_participant.active_participant,
                ),
            )
            participant = (
                await session.exec(
                    select(db.WorkflowUserParticipant)
                    .where(db.WorkflowUserParticipant.workflow_definition_id == workflow_definition_id)
                    .where(db.WorkflowUserParticipant.user_id == participant_id)
                    .with_for_update()
                )
            ).one()

            for key, value in update_participant.model_dump(exclude_unset=True).items():
                setattr(participant, key, value)

            session.add(participant)

            await session.commit()
            await session.refresh(participant)

        return convert.workflow_participant_from_db(model=participant)

    async def get_workflow_definition_defaults(self) -> NewWorkflowDefinition:
        return NewWorkflowDefinition(
            label="New Workflow",
            start_state_id="start",
            states=[],
            transitions=[],
            conversation_definitions=[],
            assistant_definitions=[],
            context_transfer_instruction=default_context_transfer_instruction,
        )

    # Workflow Run

    async def create_workflow_run(self, new_workflow_run: NewWorkflowRun) -> WorkflowRun:
        async with self._get_session() as session:
            workflow_definition = await self.get_workflow_definition(
                workflow_definition_id=new_workflow_run.workflow_definition_id
            )

            workflow_run = db.WorkflowRun(
                workflow_definition_id=new_workflow_run.workflow_definition_id,
                data={
                    "title": new_workflow_run.title,
                    "current_state_id": workflow_definition.start_state_id,
                    "conversation_mappings": [],
                    "assistant_mappings": [],
                    "metadata": new_workflow_run.metadata,
                },
            )
            session.add(workflow_run)
            await session.commit()
            await session.refresh(workflow_run)

        # initialize workflow
        await self.ensure_configuration_for_workflow_state(
            workflow_run_id=workflow_run.workflow_run_id,
        )

        return convert.workflow_run_from_db(model=workflow_run)

    async def get_workflow_run(self, workflow_run_id: uuid.UUID) -> WorkflowRun:
        async with self._get_session() as session:
            workflow_run = (
                await session.exec(
                    query.select(db.WorkflowRun).where(db.WorkflowRun.workflow_run_id == workflow_run_id)
                )
            ).one_or_none()
            if workflow_run is None:
                raise exceptions.NotFoundError()

        return convert.workflow_run_from_db(model=workflow_run)

    async def get_workflow_runs(
        self, user_principal: auth.UserPrincipal, workflow_definition_id: uuid.UUID | None = None
    ) -> WorkflowRunList:
        async with self._get_session() as session:
            workflow_query = query.select_workflow_runs_for(user_principal=user_principal)
            if workflow_definition_id is not None:
                workflow_query = (
                    select(db.WorkflowRun)
                    .join(db.WorkflowDefinition)
                    .where(db.WorkflowDefinition.workflow_definition_id == workflow_definition_id)
                )
            workflow_runs = await session.exec(workflow_query)
            return convert.workflow_run_list_from_db(models=workflow_runs)

    async def update_workflow_run(
        self, workflow_run_id: uuid.UUID, update_workflow_run: UpdateWorkflowRun
    ) -> WorkflowRun:
        async with self._get_session() as session:
            workflow_run = (
                await session.exec(
                    query.select(db.WorkflowRun)
                    .where(db.WorkflowRun.workflow_run_id == workflow_run_id)
                    .with_for_update()
                )
            ).one_or_none()
            if workflow_run is None:
                raise exceptions.NotFoundError()

            data = workflow_run.data.copy()
            updates = update_workflow_run.model_dump(exclude_unset=True)
            data.update(updates)
            workflow_run.data = data

            session.add(workflow_run)
            await session.commit()
            await session.refresh(workflow_run)

        return convert.workflow_run_from_db(model=workflow_run)

    async def get_workflow_run_assistants(self, workflow_run_id: uuid.UUID) -> AssistantList:
        workflow_run = await self.get_workflow_run(workflow_run_id=workflow_run_id)
        assistants = []
        for assistant_mapping in workflow_run.assistant_mappings:
            assistant = await self._assistant_controller.get_assistant(
                assistant_id=uuid.UUID(assistant_mapping.assistant_id)
            )
            if assistant is not None:
                assistants.append(assistant)
        return AssistantList(assistants=assistants)

    async def switch_workflow_run_state(
        self, workflow_run_id: uuid.UUID, target_state_id: str, metadata: dict[str, Any] | None = None
    ) -> WorkflowRun:
        # save the data
        async with self._get_session() as session:
            workflow_run = (
                await session.exec(
                    query.select(db.WorkflowRun)
                    .where(db.WorkflowRun.workflow_run_id == workflow_run_id)
                    .with_for_update()
                )
            ).one_or_none()
            if workflow_run is None:
                raise exceptions.NotFoundError()

            # update workflow run state
            data = workflow_run.data.copy()

            # get prior state id for handling state changes
            prior_state_id = data["current_state_id"]
            # ensure target state is different from current state
            if prior_state_id == target_state_id:
                raise exceptions.RuntimeError(detail="target state is the same as the current state")

            updates = {"current_state_id": str(target_state_id)}
            data.update(updates)
            workflow_run.data = data

            session.add(workflow_run)
            await session.commit()
            await session.refresh(workflow_run)

        # apply state change
        try:
            await self.handle_workflow_state_changed(
                workflow_run_id=workflow_run_id, prior_state_id=prior_state_id, metadata=metadata
            )
        except Exception as e:
            raise exceptions.RuntimeError(
                detail=f"failed to notify workflow state change: {e}",
            ) from e

        # reload workflow run to get updated state
        return await self.get_workflow_run(workflow_run_id=workflow_run_id)

    async def delete_workflow_run(self, user_principal: auth.UserPrincipal, workflow_run_id: uuid.UUID) -> None:
        # TODO: implement delete logic, including cleaning up all associated conversations
        # and assistants hard/soft-delete, etc.
        async with self._get_session() as session:
            workflow_run = (
                await session.exec(
                    query.select_workflow_runs_for(user_principal=user_principal).where(
                        db.WorkflowRun.workflow_run_id == workflow_run_id
                    )
                )
            ).one_or_none()
            if workflow_run is None:
                raise exceptions.NotFoundError()

            await session.delete(workflow_run)
            await session.commit()

    #
    # Private methods
    #

    async def handle_workflow_state_changed(
        self,
        workflow_run_id: uuid.UUID,
        prior_state_id: str,
        metadata: dict[str, Any] | None = None,
    ) -> None:
        # ensure conversation and assistant configuration for new state
        try:
            await self.ensure_configuration_for_workflow_state(
                workflow_run_id=workflow_run_id,
                prior_state_id=prior_state_id,
            )
        except Exception as e:
            raise exceptions.RuntimeError(
                detail=f"failed to ensure configuration for new state while switching state: {e}",
            ) from e

        # get updated workflow run and definition
        workflow_run = await self.get_workflow_run(workflow_run_id=workflow_run_id)
        workflow_definition = await self.get_workflow_definition(
            workflow_definition_id=workflow_run.workflow_definition_id
        )

        # get prior state info
        prior_state = next((state for state in workflow_definition.states if state.id == prior_state_id), None)
        if prior_state is None:
            raise exceptions.RuntimeError(
                detail="prior state not found while notifying state change",
            )

        # get prior conversation id
        prior_conversation_id = self.get_conversation_id_for_workflow_state(
            workflow_run=workflow_run,
            workflow_definition=workflow_definition,
            target_state_id=prior_state_id,
        )

        # get current state info
        workflow_state = next(
            (state for state in workflow_definition.states if state.id == workflow_run.current_state_id), None
        )
        if workflow_state is None:
            raise exceptions.RuntimeError(
                detail="current state not found while notifying state change",
            )

        # send state change message to prior conversation
        try:
            await self._conversation_controller.create_conversation_message(
                conversation_id=uuid.UUID(prior_conversation_id),
                new_message=NewConversationMessage(
                    message_type=MessageType.notice,
                    content=f"workflow state changed to {workflow_state.label}",
                    metadata={
                        **(metadata or {}),
                        "workflow_run_updated": str(workflow_run_id),
                    },
                ),
                principal=service_user_principals.workflow,
            )
        except Exception as e:
            raise exceptions.RuntimeError(
                detail=f"failed to send state change message: {e}",
            ) from e

        # get current conversation id
        current_conversation_id = self.get_conversation_id_for_workflow_state(
            workflow_run=workflow_run,
            workflow_definition=workflow_definition,
            target_state_id=workflow_run.current_state_id,
        )

        if current_conversation_id == prior_conversation_id:
            # no conversation change, exit early
            return

        # conversation changed, handle conversation change
        try:
            await self.handle_workflow_conversation_changed(
                workflow_run_id=workflow_run_id,
                prior_state_id=prior_state_id,
                prior_conversation_id=prior_conversation_id,
                current_conversation_id=current_conversation_id,
            )
        except Exception as e:
            raise exceptions.RuntimeError(
                detail=f"failed to handle conversation change: {e}",
            ) from e

    async def handle_workflow_conversation_changed(
        self,
        workflow_run_id: uuid.UUID,
        prior_state_id: str,
        prior_conversation_id: str,
        current_conversation_id: str,
    ) -> None:
        # get workflow run and definition
        workflow_run = await self.get_workflow_run(workflow_run_id=workflow_run_id)
        workflow_definition = await self.get_workflow_definition(
            workflow_definition_id=workflow_run.workflow_definition_id
        )

        # set all assistants in prior conversation to inactive
        try:
            await self.deactivate_all_assistants_in_conversation(
                workflow_run=workflow_run,
                conversation_id=uuid.UUID(prior_conversation_id),
            )
        except Exception as e:
            raise exceptions.RuntimeError(
                detail=f"failed to set all assistants in current conversation to inactive: {e}",
            ) from e

        # get current state info
        workflow_state = next(
            (state for state in workflow_definition.states if state.id == workflow_run.current_state_id), None
        )
        if workflow_state is None:
            raise exceptions.RuntimeError(
                detail="current state not found while notifying state change",
            )

        # get conversation definition for workflow state
        conversation_definition = next(
            (
                possible_conversation_definition
                for possible_conversation_definition in workflow_definition.conversation_definitions
                if possible_conversation_definition.id == workflow_state.conversation_definition_id
            ),
            None,
        )
        if conversation_definition is None:
            raise exceptions.RuntimeError(
                detail="conversation definition not found while notifying state change",
            )

        # inform the previous conversation of the conversation change
        try:
            await self._conversation_controller.create_conversation_message(
                conversation_id=uuid.UUID(prior_conversation_id),
                new_message=NewConversationMessage(
                    message_type=MessageType.notice,
                    content=f"workflow conversation changed to {conversation_definition.title}",
                    metadata={
                        "workflow_run_updated": str(workflow_run.id),
                    },
                ),
                principal=service_user_principals.workflow,
            )
        except Exception as e:
            raise exceptions.RuntimeError(
                detail=f"failed to inform previous conversation of conversation change: {e}",
            ) from e

        # transfer context from previous conversation to new conversation
        try:
            await self.transfer_context_if_applicable(
                workflow_run_id=workflow_run_id,
                source_state_id=prior_state_id,
                target_state_id=workflow_run.current_state_id,
            )
        except Exception as e:
            raise exceptions.RuntimeError(
                detail=f"failed to transfer context from previous conversation to new conversation: {e}",
            ) from e

        # inform the new conversation of the conversation change
        try:
            await self._conversation_controller.create_conversation_message(
                conversation_id=uuid.UUID(current_conversation_id),
                new_message=NewConversationMessage(
                    message_type=MessageType.notice,
                    content="workflow conversation changed to here",
                    metadata={
                        "workflow_run_updated": str(workflow_run.id),
                    },
                ),
                principal=service_user_principals.workflow,
            )
        except Exception as e:
            raise exceptions.RuntimeError(
                detail=f"failed to inform new conversation of conversation change: {e}",
            ) from e

    async def ensure_configuration_for_workflow_state(
        self, workflow_run_id: uuid.UUID, prior_state_id: str | None = None
    ) -> None:
        # ensure conversation is configured
        conversation = await self.ensure_configuration_of_conversation_for_workflow_state(
            workflow_run_id=workflow_run_id,
            prior_state_id=prior_state_id,
        )

        # ensure assistants are configured
        await self.ensure_configuration_of_conversation_assistants_for_workflow_state(
            workflow_run_id=workflow_run_id,
            conversation=conversation,
        )

    async def ensure_configuration_of_conversation_for_workflow_state(
        self,
        workflow_run_id: uuid.UUID,
        prior_state_id: str | None = None,
    ) -> Conversation:
        # get workflow run and definition
        workflow_run = await self.get_workflow_run(workflow_run_id=workflow_run_id)
        workflow_definition = await self.get_workflow_definition(
            workflow_definition_id=workflow_run.workflow_definition_id
        )

        # get current state
        workflow_state = next(
            (state for state in workflow_definition.states if state.id == workflow_run.current_state_id), None
        )
        if workflow_state is None:
            raise exceptions.RuntimeError(
                detail="current state not found while ensuring conversation configuration",
            )

        # determine if we should force a new conversation instance
        if prior_state_id is not None and workflow_state.force_new_conversation_instance:
            # we are both coming from a prior state and the current state requires a new conversation instance
            conversation = await self.create_conversation_for_workflow_state(
                workflow_run_id=workflow_run_id,
                prior_state_id=prior_state_id,
            )
            # notify the new conversation that it is a new instance
            try:
                await self._conversation_controller.create_conversation_message(
                    conversation_id=conversation.id,
                    new_message=NewConversationMessage(
                        message_type=MessageType.notice,
                        content="new conversation instance created...",
                    ),
                    principal=service_user_principals.workflow,
                )
            except Exception as e:
                raise exceptions.RuntimeError(
                    detail="failed to inform new conversation of new instance creation",
                ) from e
            return conversation

        # check if conversation exists
        conversation_id = next(
            (
                possible_conversation.conversation_id
                for possible_conversation in workflow_run.conversation_mappings
                if possible_conversation.conversation_definition_id == workflow_state.conversation_definition_id
            ),
            None,
        )
        if conversation_id is None:
            # no conversation found, create new conversation
            return await self.create_conversation_for_workflow_state(
                workflow_run_id=workflow_run_id,
                prior_state_id=prior_state_id,
            )

        # get existing conversation
        try:
            conversation = await self._conversation_controller.get_conversation(
                conversation_id=uuid.UUID(conversation_id),
                principal=service_user_principals.workflow,
            )
        except Exception as e:
            raise exceptions.RuntimeError(
                detail=f"failed to load conversation while ensuring conversation configuration: {e}",
            ) from e
        if conversation is None:
            raise exceptions.RuntimeError(
                detail="conversation not loaded while ensuring conversation configuration",
            )

        # get conversation definition
        conversation_definition = next(
            (
                possible_conversation_definition
                for possible_conversation_definition in workflow_definition.conversation_definitions
                if possible_conversation_definition.id == workflow_state.conversation_definition_id
            ),
            None,
        )
        if conversation_definition is None:
            raise exceptions.RuntimeError(
                detail="conversation definition not found while ensuring conversation configuration",
            )

        # update conversation title if it differs from the state
        if conversation.title != conversation_definition.title:
            conversation = await self.update_conversation_title(
                conversation_id=conversation.id,
                new_title=conversation_definition.title,
            )

        return conversation

    async def ensure_configuration_of_conversation_assistants_for_workflow_state(
        self,
        workflow_run_id: uuid.UUID,
        conversation: Conversation,
    ) -> None:
        # get workflow run and definition
        workflow_run = await self.get_workflow_run(workflow_run_id=workflow_run_id)
        workflow_definition = await self.get_workflow_definition(
            workflow_definition_id=workflow_run.workflow_definition_id
        )

        # get current state info
        workflow_state = next(
            (state for state in workflow_definition.states if state.id == workflow_run.current_state_id), None
        )
        if workflow_state is None:
            raise exceptions.RuntimeError(
                detail="current state not found while ensuring assistant configuration",
            )

        # get all current conversation participants
        try:
            conversation_participants = (
                await self._conversation_controller.get_conversation_participants(
                    conversation_id=conversation.id,
                    principal=service_user_principals.workflow,
                )
            ).participants
        except Exception as e:
            raise exceptions.RuntimeError(
                detail=f"failed to load conversation participants while ensuring assistant configuration: {e}",
            ) from e

        # get the assistants from conversation participants
        assistant_participants = [
            possible_assistant
            for possible_assistant in conversation_participants
            if possible_assistant.role == ParticipantRole.assistant
        ]

        # track changes to assistant mappings
        updated_assistant_mappings = workflow_run.assistant_mappings.copy()

        # ensure all assistants are configured
        for assistant_data in workflow_state.assistant_data_list:
            # get assistant definition
            assistant_definition = next(
                (
                    possible_assistant_definition
                    for possible_assistant_definition in workflow_definition.assistant_definitions
                    if possible_assistant_definition.id == assistant_data.assistant_definition_id
                ),
                None,
            )
            if assistant_definition is None:
                raise exceptions.RuntimeError(
                    detail="assistant definition not found while ensuring assistant configuration",
                )

            # check if assistant exists
            assistant_id = next(
                (
                    possible_assistant_mapping.assistant_id
                    for possible_assistant_mapping in workflow_run.assistant_mappings
                    if possible_assistant_mapping.assistant_definition_id == assistant_data.assistant_definition_id
                ),
                None,
            )
            if assistant_id is None:
                # no assistant found, create new assistant
                # create new assistant instance
                try:
                    assistant = await self._assistant_controller.create_assistant(
                        new_assistant=NewAssistant(
                            name=assistant_definition.name,
                            metadata={
                                "workflow_run_id": str(workflow_run.id),
                            },
                            assistant_service_id=assistant_definition.assistant_service_id,
                        ),
                        user_principal=service_user_principals.workflow,
                    )
                except Exception as e:
                    raise exceptions.RuntimeError(
                        detail=f"failed to create assistant while ensuring assistant configuration: {e}",
                    ) from e
                # add assistant to workflow run assistant mappings
                updated_assistant_mappings.append(
                    WorkflowAssistantMapping(
                        assistant_id=str(assistant.id),
                        assistant_definition_id=assistant_definition.id,
                    )
                )
                # add assistant to conversation
                try:
                    await self._conversation_controller.add_or_update_conversation_participant(
                        conversation_id=conversation.id,
                        participant_id=str(assistant.id),
                        update_participant=UpdateParticipant(
                            active_participant=True,
                        ),
                        principal=service_user_principals.workflow,
                    )
                except Exception as e:
                    raise exceptions.RuntimeError(
                        detail=f"failed to add assistant to conversation while ensuring assistant configuration: {e}",
                    ) from e
                # inform conversation of assistant joining
                try:
                    await self._conversation_controller.create_conversation_message(
                        conversation_id=conversation.id,
                        new_message=NewConversationMessage(
                            message_type=MessageType.notice,
                            content=f"{assistant.name} joined conversation...",
                        ),
                        principal=service_user_principals.workflow,
                    )
                except Exception as e:
                    raise exceptions.RuntimeError(
                        detail=f"failed to inform conversation of assistant joining: {e}",
                    ) from e
            else:
                # load assistant instance
                try:
                    assistant = await self._assistant_controller.get_assistant(
                        assistant_id=uuid.UUID(assistant_id),
                    )
                except Exception as e:
                    raise exceptions.RuntimeError(
                        detail=f"failed to load assistant while ensuring assistant configuration: {e}",
                    ) from e

                # check if assistant exist in conversation already
                assistant_participant = next(
                    (
                        possible_assistant
                        for possible_assistant in assistant_participants
                        if possible_assistant.id == str(assistant_id)
                    ),
                    None,
                )
                if assistant_participant is None:
                    # assistant is not in the conversation
                    # add assistant to conversation
                    try:
                        await self._conversation_controller.add_or_update_conversation_participant(
                            conversation_id=conversation.id,
                            participant_id=str(assistant.id),
                            update_participant=UpdateParticipant(
                                active_participant=True,
                            ),
                            principal=service_user_principals.workflow,
                        )
                    except Exception as e:
                        raise exceptions.RuntimeError(
                            detail=(
                                f"failed to add assistant to conversation while ensuring assistant configuration: {e}"
                            ),
                        ) from e
                    # inform conversation of assistant joining
                    try:
                        await self._conversation_controller.create_conversation_message(
                            conversation_id=conversation.id,
                            new_message=NewConversationMessage(
                                message_type=MessageType.notice,
                                content=f"{assistant.name} joined conversation...",
                            ),
                            principal=service_user_principals.workflow,
                        )
                    except Exception as e:
                        raise exceptions.RuntimeError(
                            detail=f"failed to inform conversation of assistant joining: {e}",
                        ) from e
            if assistant is None:
                raise exceptions.RuntimeError(
                    detail="assistant not loaded while ensuring assistant configuration",
                )

            # update assistant name if it differs from the state
            if assistant.name != assistant_definition.name:
                current_name = assistant.name
                # update assistant name
                try:
                    assistant = await self._assistant_controller.update_assistant(
                        assistant_id=assistant.id,
                        update_assistant=UpdateAssistant(
                            name=assistant_definition.name,
                        ),
                    )
                except Exception as e:
                    raise exceptions.RuntimeError(
                        detail=f"failed to update assistant name while ensuring assistant configuration: {e}",
                    ) from e
                # add assistant name change to conversation
                try:
                    await self._conversation_controller.create_conversation_message(
                        conversation_id=conversation.id,
                        new_message=NewConversationMessage(
                            message_type=MessageType.notice,
                            content=f"{current_name} changed name to {assistant.name}",
                        ),
                        principal=service_user_principals.workflow,
                    )
                except Exception as e:
                    raise exceptions.RuntimeError(
                        detail=f"failed to add assistant name change to conversation: {e}",
                    ) from e

            # check to see if assistant config differs from the state config
            try:
                assistant_config = await self._assistant_controller.get_assistant_config(
                    assistant_id=assistant.id,
                )
            except Exception as e:
                raise exceptions.RuntimeError(
                    detail=f"failed to load assistant config while ensuring assistant configuration: {e}",
                ) from e
            if assistant_config.config != assistant_data.config_data:
                # update assistant config to match state config
                try:
                    await self._assistant_controller.update_assistant_config(
                        assistant_id=assistant.id,
                        updated_config=ConfigPutRequestModel(
                            config=assistant_data.config_data,
                        ),
                    )
                except Exception as e:
                    raise exceptions.RuntimeError(
                        detail=f"failed to update assistant config while ensuring assistant configuration: {e}",
                    ) from e

                # inform conversation of config change
                try:
                    await self._conversation_controller.create_conversation_message(
                        conversation_id=conversation.id,
                        new_message=NewConversationMessage(
                            message_type=MessageType.notice,
                            content=f"{assistant.name} config updated...",
                        ),
                        principal=service_user_principals.workflow,
                    )
                except Exception as e:
                    raise exceptions.RuntimeError(
                        detail=f"failed to inform conversation of assistant config change: {e}",
                    ) from e

        # update workflow run assistant mappings
        try:
            workflow_run = await self.update_workflow_run_mappings(
                workflow_run_id=workflow_run.id,
                update_workflow_run_mappings=UpdateWorkflowRunMappings(
                    assistant_mappings=updated_assistant_mappings,
                ),
            )
        except Exception as e:
            raise exceptions.RuntimeError(
                detail=f"failed to update workflow run assistant mappings: {e}",
            ) from e

        # remove assistants not in the state
        for assistant_participant in assistant_participants:
            # check if assistant is in the state
            assistant_mapping = next(
                (
                    possible_assistant_mapping
                    for possible_assistant_mapping in workflow_run.assistant_mappings
                    if possible_assistant_mapping.assistant_id == assistant_participant.id
                ),
                None,
            )
            if assistant_mapping is None:
                raise exceptions.RuntimeError(
                    detail=f"assistant mapping not found while removing {assistant_participant.name} from conversation",
                )
            assistant_data = next(
                (
                    possible_assistant_data
                    for possible_assistant_data in workflow_state.assistant_data_list
                    if possible_assistant_data.assistant_definition_id == assistant_mapping.assistant_definition_id
                ),
                None,
            )
            if assistant_data is None:
                # assistant is not in the state
                # remove assistant from conversation
                try:
                    await self._conversation_controller.add_or_update_conversation_participant(
                        conversation_id=conversation.id,
                        participant_id=assistant_participant.id,
                        update_participant=UpdateParticipant(
                            active_participant=False,
                        ),
                        principal=service_user_principals.workflow,
                    )
                except Exception as e:
                    raise exceptions.RuntimeError(
                        detail=(
                            (
                                f"failed to remove {assistant_participant.name} from conversation"
                                " while ensuring assistant configuration"
                            ),
                        ),
                    ) from e
                # inform conversation of assistant leaving
                try:
                    await self._conversation_controller.create_conversation_message(
                        conversation_id=conversation.id,
                        new_message=NewConversationMessage(
                            message_type=MessageType.notice,
                            content=f"{assistant_participant.name} left conversation...",
                        ),
                        principal=service_user_principals.workflow,
                    )
                except Exception as e:
                    raise exceptions.RuntimeError(
                        detail=f"failed to inform conversation of {assistant_participant.name} leaving",
                    ) from e

    async def perform_transition_if_applicable(
        self,
        workflow_run_id: uuid.UUID,
    ) -> None:

        # get workflow run and definition
        workflow_run = await self.get_workflow_run(workflow_run_id=workflow_run_id)
        workflow_definition = await self.get_workflow_definition(
            workflow_definition_id=workflow_run.workflow_definition_id
        )

        # get current state info
        workflow_state = next(
            (state for state in workflow_definition.states if state.id == workflow_run.current_state_id), None
        )
        if workflow_state is None:
            raise exceptions.RuntimeError(
                detail="current state not found while evaluating transitions",
            )

        try:
            current_conversation_id = self.get_conversation_id_for_workflow_state(
                workflow_run=workflow_run,
                workflow_definition=workflow_definition,
                target_state_id=workflow_run.current_state_id,
            )
        except Exception as e:
            raise exceptions.RuntimeError(
                detail=f"failed to get conversation id for current state while evaluating transitions: {e}",
            ) from e

        # get chat history
        try:
            chat_history = await self.get_formatted_chat_history(
                principal=service_user_principals.workflow,
                conversation_id=current_conversation_id,
            )
        except Exception as e:
            raise exceptions.RuntimeError(
                detail=f"failed to get chat history while evaluating transitionsJ: {e}",
            ) from e

        # evaluate outlets
        for outlet in workflow_state.outlets:
            if outlet.prompts.evaluate_transition is None or outlet.prompts.evaluate_transition.strip() == "":
                continue

            # evaluate outlet condition
            should_transition, metadata = await self.execute_transition_evaluation_query(
                transition_evaluation_prompt=outlet.prompts.evaluate_transition,
                chat_history=chat_history,
            )

            # create a log message with the evaluation result
            try:
                await self._conversation_controller.create_conversation_message(
                    conversation_id=uuid.UUID(current_conversation_id),
                    new_message=NewConversationMessage(
                        message_type=MessageType.log,
                        content=f"Transition evaluation result [outlet: {outlet.label}]: {should_transition}",
                        metadata=metadata,
                    ),
                    principal=service_user_principals.workflow,
                )
            except Exception as e:
                raise exceptions.RuntimeError(
                    detail=f"failed to create log message with evaluation result: {e}",
                ) from e

            if not should_transition:
                continue

            # get transition info
            transition = next(
                (
                    possible_transition
                    for possible_transition in workflow_definition.transitions
                    if possible_transition.source_outlet_id == outlet.id
                ),
                None,
            )

            # determine target state id
            if transition is not None:
                target_state_id = transition.target_state_id
            else:
                # no transition found, default to start state
                target_state_id = workflow_definition.start_state_id

            # transition to target state
            try:
                workflow_run = await self.switch_workflow_run_state(
                    workflow_run_id=workflow_run.id,
                    target_state_id=target_state_id,
                    metadata=metadata,
                )
            except Exception as e:
                raise exceptions.RuntimeError(
                    detail=f"failed to transition to target state: {e}",
                ) from e

    async def transfer_context_if_applicable(
        self,
        workflow_run_id: uuid.UUID,
        source_state_id: str,
        target_state_id: str,
    ) -> None:
        # check if there is a transition to target state
        transition = await self.find_transition_by_states(
            workflow_run_id=workflow_run_id,
            source_state_id=source_state_id,
            target_state_id=target_state_id,
        )

        if transition is None:
            # no transition found, exit early
            return

        # get workflow run and definition
        workflow_run = await self.get_workflow_run(workflow_run_id=workflow_run_id)
        workflow_definition = await self.get_workflow_definition(
            workflow_definition_id=workflow_run.workflow_definition_id
        )

        # get source state info
        source_state = next((state for state in workflow_definition.states if state.id == source_state_id), None)
        if source_state is None:
            raise exceptions.RuntimeError(
                detail="source state not found while transferring context",
            )

        # get outlet for transition
        outlet = next(
            (
                possible_outlet
                for possible_outlet in source_state.outlets
                if possible_outlet.id == transition.source_outlet_id
            ),
            None,
        )
        if outlet is None:
            raise exceptions.RuntimeError(
                detail="outlet not found while transferring context",
            )

        # get context transfer prompt
        context_transfer_request = outlet.prompts.context_transfer
        if context_transfer_request is None or context_transfer_request.strip() == "":
            # no context transfer prompt, exit early
            return

        # get conversation id for source state
        source_conversation_id = self.get_conversation_id_for_workflow_state(
            workflow_run=workflow_run,
            workflow_definition=workflow_definition,
            target_state_id=source_state_id,
        )

        # get conversation id for target state
        target_conversation_id = self.get_conversation_id_for_workflow_state(
            workflow_run=workflow_run,
            workflow_definition=workflow_definition,
            target_state_id=target_state_id,
        )

        if source_conversation_id == target_conversation_id:
            # no need to transfer context to the same conversation
            return

        # proceed to execute context transfer

        # get chat history
        try:
            chat_history = await self.get_formatted_chat_history(
                principal=service_user_principals.workflow,
                conversation_id=source_conversation_id,
            )
        except Exception as e:
            raise exceptions.RuntimeError(
                detail=f"failed to get chat history while transferring context: {e}",
            ) from e

        # generate context transfer response
        try:
            context_transfer_response, metadata = await self.execute_context_transfer_generation(
                context_transfer_instruction=workflow_definition.context_transfer_instruction,
                context_transfer_request=context_transfer_request,
                chat_history=chat_history,
            )
        except Exception as e:
            raise exceptions.RuntimeError(
                detail=f"failed to execute context transfer generation: {e}",
            ) from e

        # send context transfer response as message to conversation
        try:
            await self._conversation_controller.create_conversation_message(
                conversation_id=uuid.UUID(target_conversation_id),
                new_message=NewConversationMessage(
                    message_type=MessageType.chat,
                    content=context_transfer_response,
                    metadata=metadata,
                ),
                principal=service_user_principals.workflow,
            )
        except Exception as e:
            raise exceptions.RuntimeError(
                detail=f"failed to send context transfer response as message to conversation: {e}",
            ) from e

    async def execute_transition_evaluation_query(
        self,
        transition_evaluation_prompt: str,
        chat_history: list[str],
    ) -> Tuple[bool, dict[str, Any]]:

        # history message content
        history_message_content = "<CHAT_HISTORY>" + "\n".join(chat_history) + "</CHAT_HISTORY>"

        # instruction evaluation prompt
        instruction_message_content = (
            "Evaluate the <CHAT_HISTORY/> and determine if the following <EVALUATION_CRITERIA/>"
            f" has occurred: <EVALUATION_CRITERIA>{transition_evaluation_prompt}</EVALUATION_CRITERIA>"
        )

        # format message content
        format_message_content = "Answer only with 'true' or 'false'."

        model = settings.workflow.azure_openai_deployment
        messages: list[openai.types.chat.ChatCompletionMessageParam] = [
            {
                "role": "system",
                "name": "system",
                "content": history_message_content,
            },
            {
                "role": "user",
                "name": "user",
                "content": instruction_message_content,
            },
            {
                "role": "system",
                "name": "system",
                "content": format_message_content,
            },
        ]

        try:
            async with azure_openai_client() as client:
                completion = await client.chat.completions.create(
                    model=model,
                    temperature=0.0,
                    messages=messages,
                )
        except Exception as e:
            raise exceptions.RuntimeError(
                detail=f"failed calling Azure OpenAI service while evaluating transitions: {e}",
            ) from e

        completion_content = completion.choices[0].message.content

        value = False if completion_content is None else completion_content.lower().strip() == "true"

        return (
            value,
            {
                "debug": {
                    "model": model,
                    "completion_request": messages,
                    "completion_response": completion.model_dump(),
                }
            },
        )

    async def execute_context_transfer_generation(
        self,
        context_transfer_instruction: str,
        context_transfer_request: str,
        chat_history: list[str],
    ) -> Tuple[str, dict[str, Any]]:

        # history message content
        history_message_content = "<CHAT_HISTORY>" + "\n".join(chat_history) + "</CHAT_HISTORY>"

        # instruction evaluation prompt
        instruction_message_content = (
            "Generate a response based on the <CHAT_HISTORY/> and the following <CONTEXT_TRANSFER_REQUEST/>."
            f" {context_transfer_instruction}:"
            f" <CONTEXT_TRANSFER_REQUEST>{context_transfer_request}</CONTEXT_TRANSFER_REQUEST>"
        )

        model = settings.workflow.azure_openai_deployment
        messages: list[openai.types.chat.ChatCompletionMessageParam] = [
            {
                "role": "system",
                "name": "system",
                "content": history_message_content,
            },
            {
                "role": "user",
                "name": "user",
                "content": instruction_message_content,
            },
        ]

        try:
            async with azure_openai_client() as client:
                completion = await client.chat.completions.create(
                    model=model,
                    temperature=0.0,
                    messages=messages,
                )
        except Exception as e:
            raise exceptions.RuntimeError(
                detail=f"failed calling Azure OpenAI service while generating context transfer: {e}",
            ) from e

        completion_content = completion.choices[0].message.content

        return (
            completion_content or "",
            {
                "debug": {
                    "model": model,
                    "completion_request": messages,
                    "completion_response": completion.model_dump(),
                }
            },
        )

    async def get_formatted_chat_history(
        self,
        principal: auth.ActorPrincipal,
        conversation_id: str,
    ) -> list[str]:
        # build context for evaluating transitions
        try:
            messages = await self._conversation_controller.get_messages(
                conversation_id=uuid.UUID(conversation_id),
                principal=principal,
            )
        except Exception as e:
            raise exceptions.RuntimeError(
                detail=f"failed to load messages while evaluating transitions: {e}",
            ) from e

        try:
            participants = await self._conversation_controller.get_conversation_participants(
                conversation_id=uuid.UUID(conversation_id),
                principal=principal,
                include_inactive=True,
            )
        except Exception as e:
            raise exceptions.RuntimeError(
                detail=f"failed to load participants while evaluating transitions: {e}",
            ) from e

        def format_message_for_history(message: ConversationMessage) -> str:
            participant = next(
                (
                    possible_participant
                    for possible_participant in participants.participants
                    if possible_participant.id == message.sender.participant_id
                ),
                None,
            )
            if participant is None:
                raise exceptions.RuntimeError(
                    detail="participant not found while formatting message for history",
                )
            return f"{participant.name}: {message.content}"

        chat_history = [
            format_message_for_history(message)
            for message in messages.messages
            if message.message_type == MessageType.chat
        ]

        max_tokens = 4000 * 4  # roughly 4 characters per token
        # remove from the beginning of the history until the length is less than max_tokens
        while len("".join(chat_history)) > max_tokens:
            chat_history.pop(0)

        return chat_history

    async def deactivate_all_assistants_in_conversation(
        self, workflow_run: WorkflowRun, conversation_id: uuid.UUID
    ) -> None:
        # get conversation participants
        try:
            participants = await self._conversation_controller.get_conversation_participants(
                conversation_id=conversation_id,
                principal=service_user_principals.workflow,
            )
        except Exception as e:
            raise exceptions.RuntimeError(
                detail=f"failed to get conversation participants while setting all assistants inactive: {e}",
            ) from e

        # set all assistants to inactive
        for participant in participants.participants:
            if not participant.active_participant or participant.id not in [
                mapping.assistant_id for mapping in workflow_run.assistant_mappings
            ]:
                continue

            try:
                await self._conversation_controller.add_or_update_conversation_participant(
                    conversation_id=conversation_id,
                    participant_id=participant.id,
                    update_participant=UpdateParticipant(
                        active_participant=False,
                    ),
                    principal=service_user_principals.workflow,
                )
            except Exception as e:
                raise exceptions.RuntimeError(
                    detail=f"failed to set assistant {participant.id} to inactive: {e}",
                ) from e

            # inform conversation of assistant leaving
            try:
                await self._conversation_controller.create_conversation_message(
                    conversation_id=conversation_id,
                    new_message=NewConversationMessage(
                        message_type=MessageType.notice,
                        content=f"{participant.name} left conversation...",
                    ),
                    principal=service_user_principals.workflow,
                )
            except Exception as e:
                raise exceptions.RuntimeError(
                    detail=f"failed to inform conversation of assistant leaving: {e}",
                ) from e

    async def find_transition_by_states(
        self,
        workflow_run_id: uuid.UUID,
        source_state_id: str,
        target_state_id: str,
    ) -> WorkflowTransition | None:
        # get workflow run and definition
        workflow_run = await self.get_workflow_run(workflow_run_id=workflow_run_id)
        workflow_definition = await self.get_workflow_definition(
            workflow_definition_id=workflow_run.workflow_definition_id
        )

        # check outlets for transitions to target state
        for source_state in workflow_definition.states:
            if source_state.id != source_state_id:
                continue

            for outlet in source_state.outlets:
                # check if outlet has a transition to target state
                transition = next(
                    (
                        possible_transition
                        for possible_transition in workflow_definition.transitions
                        if possible_transition.source_outlet_id == outlet.id
                        and possible_transition.target_state_id == target_state_id
                    ),
                    None,
                )
                if transition is not None:
                    return transition

            # if no transition found, return a default transition to the start state
            # use the start_state_id as id in case it is needed again (should not be)
            return WorkflowTransition(
                id=workflow_definition.start_state_id,
                source_outlet_id=outlet.id,
                target_state_id=workflow_definition.start_state_id,
            )

    async def create_conversation_for_workflow_state(
        self,
        workflow_run_id: uuid.UUID,
        prior_state_id: str | None = None,
    ) -> Conversation:
        # get workflow run and definition
        workflow_run = await self.get_workflow_run(workflow_run_id=workflow_run_id)
        workflow_definition = await self.get_workflow_definition(
            workflow_definition_id=workflow_run.workflow_definition_id
        )

        # get current state info
        workflow_state = next(
            (state for state in workflow_definition.states if state.id == workflow_run.current_state_id), None
        )
        if workflow_state is None:
            raise exceptions.RuntimeError(
                detail="current state not found while ensuring conversation configuration",
            )

        # get conversation definition for workflow state
        conversation_definition = next(
            (
                possible_conversation_definition
                for possible_conversation_definition in workflow_definition.conversation_definitions
                if possible_conversation_definition.id == workflow_state.conversation_definition_id
            ),
            None,
        )
        if conversation_definition is None:
            raise exceptions.RuntimeError(
                detail="conversation definition not found while ensuring conversation configuration",
            )

        # create the conversation
        try:
            conversation = await self._conversation_controller.create_conversation(
                new_conversation=NewConversation(
                    title=conversation_definition.title,
                    metadata={
                        "workflow_run_id": str(workflow_run.id),
                    },
                ),
                user_principal=service_user_principals.workflow,
            )
        except Exception as e:
            raise exceptions.RuntimeError(
                detail=f"failed to create conversation while ensuring conversation configuration: {e}",
            ) from e

        # add workflow participant so that it can send messages
        try:
            await self._conversation_controller.add_or_update_conversation_participant(
                conversation_id=conversation.id,
                participant_id=service_user_principals.workflow.user_id,
                update_participant=UpdateParticipant(
                    active_participant=True,
                ),
                principal=service_user_principals.workflow,
            )
        except Exception as e:
            raise exceptions.RuntimeError(
                detail=f"failed to add workflow participant to conversation: {e}",
            ) from e

        if prior_state_id is not None:
            # get conversation id for prior state
            prior_conversation_id = self.get_conversation_id_for_workflow_state(
                workflow_run=workflow_run,
                workflow_definition=workflow_definition,
                target_state_id=prior_state_id,
            )

            # if conversation ids are different, copy user participants from prior conversation
            if prior_conversation_id != str(conversation.id):
                await self.copy_conversation_user_participants(
                    source_conversation_id=uuid.UUID(prior_conversation_id),
                    target_conversation_id=conversation.id,
                    deactivate_participants=True,
                )

        # remove any existing mappings for the conversation definition
        workflow_run.conversation_mappings = [
            mapping
            for mapping in workflow_run.conversation_mappings
            if mapping.conversation_definition_id != conversation_definition.id
        ]
        # add new mapping
        workflow_run.conversation_mappings.append(
            WorkflowConversationMapping(
                conversation_id=str(conversation.id),
                conversation_definition_id=conversation_definition.id,
            )
        )

        # update workflow run conversation mappings
        try:
            await self.update_workflow_run_mappings(
                workflow_run_id=workflow_run.id,
                update_workflow_run_mappings=UpdateWorkflowRunMappings(
                    conversation_mappings=workflow_run.conversation_mappings,
                ),
            )
        except Exception as e:
            raise exceptions.RuntimeError(
                detail=f"failed to update workflow run conversation mappings: {e}",
            ) from e

        return conversation

    async def update_conversation_title(
        self,
        conversation_id: uuid.UUID,
        new_title: str,
    ) -> Conversation:
        # get conversation
        try:
            conversation = await self._conversation_controller.get_conversation(
                conversation_id=conversation_id,
                principal=service_user_principals.workflow,
            )
        except Exception as e:
            raise exceptions.RuntimeError(
                detail=f"failed to load conversation while ensuring conversation configuration: {e}",
            ) from e
        if conversation is None:
            raise exceptions.RuntimeError(
                detail="conversation not loaded while ensuring conversation configuration",
            )

        # track current conversation title
        current_conversation_title = conversation.title

        # update conversation title
        try:
            conversation = await self._conversation_controller.update_conversation(
                conversation_id=conversation.id,
                update_conversation=UpdateConversation(
                    title=new_title,
                ),
                user_principal=service_user_principals.workflow,
            )
        except Exception as e:
            raise exceptions.RuntimeError(
                detail=f"failed to update conversation title while ensuring conversation configuration: {e}",
            ) from e

        # add conversation title change to conversation
        try:
            await self._conversation_controller.create_conversation_message(
                conversation_id=conversation.id,
                new_message=NewConversationMessage(
                    message_type=MessageType.notice,
                    content=f"conversation title changed from {current_conversation_title} to {new_title}",
                ),
                principal=service_user_principals.workflow,
            )
        except Exception as e:
            raise exceptions.RuntimeError(
                detail=f"failed to add conversation title change to conversation: {e}",
            ) from e

        return conversation

    async def copy_conversation_user_participants(
        self,
        source_conversation_id: uuid.UUID,
        target_conversation_id: uuid.UUID,
        deactivate_participants: bool = False,
    ) -> None:
        # get conversation participants
        try:
            participants = await self._conversation_controller.get_conversation_participants(
                conversation_id=source_conversation_id,
                principal=service_user_principals.workflow,
            )
        except Exception as e:
            raise exceptions.RuntimeError(
                detail=f"failed to get conversation participants while copying: {e}",
            ) from e

        # copy participants to target conversation
        for participant in participants.participants:
            if participant.role != ParticipantRole.user:
                continue

            try:
                await self._conversation_controller.add_or_update_conversation_participant(
                    conversation_id=target_conversation_id,
                    participant_id=participant.id,
                    update_participant=UpdateParticipant(
                        active_participant=False if deactivate_participants else participant.active_participant,
                    ),
                    principal=service_user_principals.workflow,
                )
            except Exception as e:
                raise exceptions.RuntimeError(
                    detail=f"failed to copy participant {participant.id} to target conversation: {e}",
                ) from e

    async def get_workflow_run_id_for_conversation(self, conversation_id: uuid.UUID) -> str | None:
        # get from db direct since we don't need to check permissions and don't have the user principal
        async with self._get_session() as session:
            possible_conversation = (
                await session.exec(select(db.Conversation).where(db.Conversation.conversation_id == conversation_id))
            ).one_or_none()
            if possible_conversation is None:
                return None

            conversation = convert.conversation_from_db(model=possible_conversation)

            if conversation.metadata is not None and "workflow_run_id" in conversation.metadata:
                return conversation.metadata["workflow_run_id"]

    async def update_workflow_run_mappings(
        self,
        workflow_run_id: uuid.UUID,
        update_workflow_run_mappings: UpdateWorkflowRunMappings,
    ) -> WorkflowRun:
        async with self._get_session() as session:
            workflow_run = (
                await session.exec(
                    query.select(db.WorkflowRun)
                    .where(db.WorkflowRun.workflow_run_id == workflow_run_id)
                    .with_for_update()
                )
            ).one_or_none()
            if workflow_run is None:
                raise exceptions.NotFoundError()

            data = workflow_run.data.copy()

            if update_workflow_run_mappings.conversation_mappings is not None:
                data["conversation_mappings"] = [
                    mapping.model_dump() for mapping in update_workflow_run_mappings.conversation_mappings
                ]

            if update_workflow_run_mappings.assistant_mappings is not None:
                data["assistant_mappings"] = [
                    mapping.model_dump() for mapping in update_workflow_run_mappings.assistant_mappings
                ]

            workflow_run.data = data

            session.add(workflow_run)
            await session.commit()
            await session.refresh(workflow_run)

        return convert.workflow_run_from_db(model=workflow_run)

    def get_conversation_id_for_workflow_state(
        self,
        workflow_run: WorkflowRun,
        workflow_definition: WorkflowDefinition,
        target_state_id: str,
    ) -> str:
        target_state = next((state for state in workflow_definition.states if state.id == target_state_id), None)
        if target_state is None:
            raise exceptions.RuntimeError(
                detail="target state not found while getting conversation id",
            )

        conversation_id = next(
            (
                possible_conversation.conversation_id
                for possible_conversation in workflow_run.conversation_mappings
                if possible_conversation.conversation_definition_id == target_state.conversation_definition_id
            ),
            None,
        )
        if conversation_id is None:
            raise exceptions.RuntimeError(
                detail="conversation mapping not found while getting conversation id",
            )

        return conversation_id


_azure_bearer_token_provider = get_bearer_token_provider(
    DefaultAzureCredential(),
    "https://cognitiveservices.azure.com/.default",
)


def azure_openai_client() -> AsyncAzureOpenAI:
    return AsyncAzureOpenAI(
        azure_endpoint=settings.workflow.azure_openai_endpoint,
        azure_deployment=settings.workflow.azure_openai_deployment,
        api_version=settings.workflow.azure_openai_api_version,
        azure_ad_token_provider=_azure_bearer_token_provider,
    )
