import datetime
import logging
import uuid
from dataclasses import dataclass
from typing import AsyncContextManager, Awaitable, Callable, Literal

from semantic_workbench_api_model.assistant_service_client import AssistantError
from semantic_workbench_api_model.workbench_model import (
    Conversation,
    ConversationEvent,
    ConversationEventType,
    ConversationList,
    ConversationMessage,
    ConversationMessageList,
    ConversationParticipant,
    ConversationParticipantList,
    MessageType,
    NewConversation,
    NewConversationMessage,
    ParticipantRole,
    UpdateConversation,
    UpdateParticipant,
)
from sqlmodel import col, select
from sqlmodel.ext.asyncio.session import AsyncSession

from .. import auth, db, query
from ..event import ConversationEventQueueItem
from . import assistant, convert, exceptions
from . import participant as participant_
from . import user as user_

logger = logging.getLogger(__name__)


@dataclass
class MessagePreview:
    conversation_id: uuid.UUID
    message: ConversationMessage


class ConversationController:
    def __init__(
        self,
        get_session: Callable[[], AsyncContextManager[AsyncSession]],
        notify_event: Callable[[ConversationEventQueueItem], Awaitable],
        assistant_controller: assistant.AssistantController,
    ) -> None:
        self._get_session = get_session
        self._notify_event = notify_event
        self._assistant_controller = assistant_controller

        self._message_previewers: list[Callable[[MessagePreview], Awaitable[None]]] = []

    def register_message_previewer(self, previewer: Callable[[MessagePreview], Awaitable[None]]) -> None:
        self._message_previewers.append(previewer)

    async def create_conversation(
        self,
        new_conversation: NewConversation,
        user_principal: auth.UserPrincipal,
    ) -> Conversation:
        async with self._get_session() as session:
            await user_.add_or_update_user_from(session=session, user_principal=user_principal)

            conversation = db.Conversation(
                owner_id=user_principal.user_id,
                title=new_conversation.title,
                meta_data=new_conversation.metadata,
            )

            session.add(conversation)

            session.add(
                db.UserParticipant(
                    conversation_id=conversation.conversation_id,
                    user_id=user_principal.user_id,
                )
            )

            await session.commit()
            await session.refresh(conversation)

        return await self.get_conversation(conversation_id=conversation.conversation_id, principal=user_principal)

    async def get_conversations(
        self,
        principal: auth.ActorPrincipal,
        include_inactive: bool = False,
    ) -> ConversationList:
        async with self._get_session() as session:
            include_inactive = include_inactive and isinstance(principal, auth.UserPrincipal)

            conversations = (
                await session.exec(
                    query.select_conversations_for(principal=principal, include_inactive=include_inactive).order_by(
                        col(db.Conversation.created_datetime).desc()
                    )
                )
            ).all()

        return convert.conversation_list_from_db(models=conversations)

    async def get_assistant_conversations(
        self,
        user_principal: auth.UserPrincipal,
        assistant_id: uuid.UUID,
    ) -> ConversationList:
        async with self._get_session() as session:
            assistant = (
                await session.exec(
                    query.select_assistants_for(user_principal=user_principal).where(
                        db.Assistant.assistant_id == assistant_id
                    )
                )
            ).one_or_none()
            if assistant is None:
                raise exceptions.NotFoundError()

            conversations = await session.exec(
                query.select_conversations_for(
                    principal=auth.AssistantPrincipal(
                        assistant_service_id=assistant.assistant_service_id, assistant_id=assistant_id
                    ),
                )
            )

            return convert.conversation_list_from_db(models=conversations)

    async def get_conversation(
        self,
        conversation_id: uuid.UUID,
        principal: auth.ActorPrincipal,
    ) -> Conversation:
        async with self._get_session() as session:
            if isinstance(principal, auth.UserPrincipal):
                await self._add_user_participant(
                    user_principal=principal, conversation_id=conversation_id, session=session
                )

            include_inactive = isinstance(principal, auth.UserPrincipal)

            conversation = (
                await session.exec(
                    query.select_conversations_for(principal=principal, include_inactive=include_inactive).where(
                        db.Conversation.conversation_id == conversation_id
                    )
                )
            ).one_or_none()
            if conversation is None:
                raise exceptions.NotFoundError()

            return convert.conversation_from_db(model=conversation)

    async def update_conversation(
        self,
        conversation_id: uuid.UUID,
        update_conversation: UpdateConversation,
        user_principal: auth.UserPrincipal,
    ) -> Conversation:
        async with self._get_session() as session:
            conversation = (
                await session.exec(
                    query.select_conversations_for(
                        principal=user_principal,
                        include_inactive=True,
                    )
                    .where(db.Conversation.conversation_id == conversation_id)
                    .with_for_update()
                )
            ).one_or_none()
            if conversation is None:
                raise exceptions.NotFoundError()

            for key, value in update_conversation.model_dump(exclude_unset=True).items():
                match key:
                    case "metadata":
                        conversation.meta_data = value
                    case _:
                        setattr(conversation, key, value)

            session.add(conversation)
            await session.commit()
            await session.refresh(conversation)

        await self._notify_event(
            ConversationEventQueueItem(
                event=ConversationEvent(
                    conversation_id=conversation.conversation_id,
                    event=ConversationEventType.conversation_updated,
                    data={
                        "conversation": convert.conversation_from_db(conversation).model_dump(),
                    },
                )
            )
        )

        return await self.get_conversation(conversation_id=conversation.conversation_id, principal=user_principal)

    async def get_conversation_participants(
        self,
        conversation_id: uuid.UUID,
        principal: auth.ActorPrincipal,
        include_inactive: bool = False,
    ) -> ConversationParticipantList:
        async with self._get_session() as session:
            if isinstance(principal, auth.UserPrincipal):
                await self._add_user_participant(
                    user_principal=principal, conversation_id=conversation_id, session=session
                )

            conversation = (
                await session.exec(
                    query.select_conversations_for(principal=principal).where(
                        db.Conversation.conversation_id == conversation_id
                    )
                )
            ).one_or_none()
            if conversation is None:
                raise exceptions.NotFoundError()

            return await participant_.get_conversation_participants(
                session=session, conversation_id=conversation.conversation_id, include_inactive=include_inactive
            )

    async def get_conversation_participant(
        self,
        conversation_id: uuid.UUID,
        participant_id: str,
        principal: auth.ActorPrincipal,
    ) -> ConversationParticipant:
        async with self._get_session() as session:
            conversation = (
                await session.exec(
                    query.select_conversations_for(principal=principal).where(
                        db.Conversation.conversation_id == conversation_id
                    )
                )
            ).one_or_none()
            if conversation is None:
                raise exceptions.NotFoundError()

            possible_user_participant = (
                await session.exec(
                    select(db.UserParticipant)
                    .where(db.UserParticipant.conversation_id == conversation.conversation_id)
                    .where(db.UserParticipant.user_id == participant_id)
                )
            ).one_or_none()
            if possible_user_participant is not None:
                return convert.conversation_participant_from_db_user(possible_user_participant)

            possible_assistant_participant = (
                await session.exec(
                    select(db.AssistantParticipant)
                    .where(db.AssistantParticipant.conversation_id == conversation.conversation_id)
                    .where(db.AssistantParticipant.assistant_id == participant_id)
                )
            ).one_or_none()
            if possible_assistant_participant is not None:
                assistant = (
                    await session.exec(
                        select(db.Assistant).where(
                            db.Assistant.assistant_id == possible_assistant_participant.assistant_id
                        )
                    )
                ).one_or_none()
                return convert.conversation_participant_from_db_assistant(
                    possible_assistant_participant, assistant=assistant
                )

        raise exceptions.NotFoundError()

    async def add_or_update_conversation_participant(
        self,
        conversation_id: uuid.UUID,
        participant_id: str,
        update_participant: UpdateParticipant,
        principal: auth.ActorPrincipal,
    ) -> ConversationParticipant:
        if update_participant.active_participant is not None and not update_participant.active_participant:
            update_participant.status = None

        updates = update_participant.model_dump(exclude_unset=True)

        async with self._get_session() as session:

            async def update_user_participant(
                conversation: db.Conversation, user: db.User
            ) -> tuple[
                ConversationParticipant,
                Literal[
                    ConversationEventType.participant_created,
                    ConversationEventType.participant_updated,
                ]
                | None,
            ]:
                new_participant = await db.insert_if_not_exists(
                    session,
                    db.UserParticipant(
                        conversation_id=conversation.conversation_id,
                        user_id=user.user_id,
                        name=user.name,
                        image=user.image,
                        service_user=user.service_user,
                        **updates,
                    ),
                )
                event_type = ConversationEventType.participant_created if new_participant else None

                participant = (
                    await session.exec(
                        select(db.UserParticipant)
                        .where(db.UserParticipant.conversation_id == conversation.conversation_id)
                        .where(db.UserParticipant.user_id == user.user_id)
                        .with_for_update()
                    )
                ).one()

                for key, value in updates.items():
                    if getattr(participant, key) != value:
                        setattr(participant, key, value)
                        event_type = event_type or ConversationEventType.participant_updated

                    if key == "status":
                        participant.status_updated_datetime = datetime.datetime.now(datetime.UTC)

                if event_type is not None:
                    session.add(participant)
                    await session.commit()
                    await session.refresh(participant)

                return convert.conversation_participant_from_db_user(participant), event_type

            async def update_assistant_participant(
                conversation: db.Conversation,
                assistant: db.Assistant,
            ) -> tuple[
                ConversationParticipant,
                Literal[
                    ConversationEventType.participant_created,
                    ConversationEventType.participant_updated,
                ]
                | None,
            ]:
                new_participant = await db.insert_if_not_exists(
                    session,
                    db.AssistantParticipant(
                        conversation_id=conversation.conversation_id,
                        assistant_id=assistant.assistant_id,
                        status=update_participant.status,
                        name=assistant.name,
                        image=assistant.image,
                    ),
                )
                event_type = ConversationEventType.participant_created if new_participant else None
                participant = (
                    await session.exec(
                        select(db.AssistantParticipant)
                        .where(db.AssistantParticipant.conversation_id == conversation.conversation_id)
                        .where(db.AssistantParticipant.assistant_id == assistant.assistant_id)
                        .with_for_update()
                    )
                ).one()

                original_participant = participant.model_copy(deep=True)

                active_participant_changed = new_participant
                if update_participant.active_participant is not None:
                    event_type = event_type or ConversationEventType.participant_updated
                    active_participant_changed = active_participant_changed or (
                        participant.active_participant != update_participant.active_participant
                    )
                    participant.active_participant = update_participant.active_participant

                if participant.status != update_participant.status:
                    event_type = event_type or ConversationEventType.participant_updated
                    participant.status = update_participant.status
                    participant.status_updated_datetime = datetime.datetime.now(datetime.UTC)

                if event_type is not None:
                    session.add(participant)
                    await session.commit()
                    await session.refresh(participant)

                if active_participant_changed and participant.active_participant:
                    try:
                        await self._assistant_controller.connect_assistant_to_conversation(
                            assistant=assistant,
                            conversation=conversation,
                            from_export=None,
                        )
                    except AssistantError:
                        logger.error(
                            f"failed to connect assistant {assistant.assistant_id} to conversation"
                            f" {conversation.conversation_id}",
                            exc_info=True,
                        )
                        session.add(original_participant)
                        await session.commit()
                        raise

                if active_participant_changed and not participant.active_participant:
                    try:
                        await self._assistant_controller.disconnect_assistant_from_conversation(
                            assistant=assistant,
                            conversation_id=conversation.conversation_id,
                        )
                    except AssistantError:
                        logger.error(
                            f"failed to disconnect assistant {assistant.assistant_id} from conversation"
                            f" {conversation.conversation_id}",
                            exc_info=True,
                        )

                return (
                    convert.conversation_participant_from_db_assistant(
                        participant,
                        assistant=assistant,
                    ),
                    event_type,
                )

            match principal:
                case auth.UserPrincipal():
                    # users can update participants in any conversation
                    conversation = (
                        await session.exec(
                            select(db.Conversation).where(db.Conversation.conversation_id == conversation_id)
                        )
                    ).one_or_none()
                    if conversation is None:
                        raise exceptions.NotFoundError()

                    assistant_id: uuid.UUID | None = None
                    try:
                        assistant_id = uuid.UUID(participant_id)
                        participant_role = "assistant"
                    except ValueError:
                        participant_role = "user"

                    match participant_role:
                        case "user":
                            # users can add any user to conversations
                            await user_.add_or_update_user_from(user_principal=principal, session=session)
                            user = (
                                await session.exec(select(db.User).where(db.User.user_id == participant_id))
                            ).one_or_none()
                            if user is None:
                                raise exceptions.NotFoundError()

                            participant, event_type = await update_user_participant(conversation, user)

                        case "assistant":
                            # users can add any of their assistants to conversation
                            assistant = (
                                await session.exec(
                                    query.select_assistants_for(user_principal=principal).where(
                                        db.Assistant.assistant_id == assistant_id
                                    )
                                )
                            ).one_or_none()
                            if assistant is None:
                                raise exceptions.NotFoundError()

                            participant, event_type = await update_assistant_participant(conversation, assistant)

                case auth.AssistantServicePrincipal():
                    # assistants can update participants in conversations they are already participants of
                    conversation = (
                        await session.exec(
                            query.select_conversations_for(principal=principal).where(
                                db.Conversation.conversation_id == conversation_id
                            )
                        )
                    ).one_or_none()

                    if conversation is None:
                        raise exceptions.NotFoundError()

                    # assistants can only update their own status
                    if participant_id != str(principal.assistant_id):
                        raise exceptions.ForbiddenError()

                    assistant = (
                        await session.exec(
                            select(db.Assistant).where(db.Assistant.assistant_id == principal.assistant_id)
                        )
                    ).one_or_none()
                    if assistant is None:
                        raise exceptions.NotFoundError()

                    if assistant.assistant_service_id != principal.assistant_service_id:
                        raise exceptions.ForbiddenError()

                    participant, event_type = await update_assistant_participant(conversation, assistant)

            if event_type is not None:
                participants = await participant_.get_conversation_participants(
                    session=session, conversation_id=conversation.conversation_id, include_inactive=True
                )

                await self._notify_event(
                    ConversationEventQueueItem(
                        event=participant_.participant_event(
                            event_type=event_type,
                            conversation_id=conversation.conversation_id,
                            participant=participant,
                            participants=participants,
                        ),
                    )
                )

            return participant

    async def create_conversation_message(
        self,
        principal: auth.ActorPrincipal,
        conversation_id: uuid.UUID,
        new_message: NewConversationMessage,
    ) -> ConversationMessage:
        async with self._get_session() as session:
            conversation = (
                await session.exec(
                    query.select_conversations_for(principal=principal).where(
                        db.Conversation.conversation_id == conversation_id
                    )
                )
            ).one_or_none()
            if conversation is None:
                raise exceptions.NotFoundError()

            if (
                new_message.id is not None
                and (
                    await session.exec(
                        query.select_conversation_messages_for(principal=principal)
                        .where(db.ConversationMessage.conversation_id == conversation_id)
                        .where(db.ConversationMessage.message_id == new_message.id)
                    )
                ).one_or_none()
                is not None
            ):
                raise exceptions.ConflictError(f"message with id {new_message.id} already exists")

            match principal:
                case auth.UserPrincipal():
                    role = "user"
                    participant_id = principal.user_id
                case auth.AssistantServicePrincipal():
                    role = "assistant"
                    participant_id = str(principal.assistant_id)

            message = db.ConversationMessage(
                conversation_id=conversation.conversation_id,
                sender_participant_role=role,
                sender_participant_id=participant_id,
                message_type=new_message.message_type.value,
                content=new_message.content,
                content_type=new_message.content_type,
                filenames=new_message.filenames or [],
                meta_data=new_message.metadata or {},
            )
            if new_message.id is not None:
                message.message_id = new_message.id

            session.add(message)
            await session.commit()
            await session.refresh(message)

        message_response = convert.conversation_message_from_db(message)

        # share message with previewers
        message_preview = MessagePreview(conversation_id=conversation_id, message=message_response)
        for previewer in self._message_previewers:
            await previewer(message_preview)

        await self._notify_event(
            ConversationEventQueueItem(
                event=ConversationEvent(
                    conversation_id=conversation_id,
                    event=ConversationEventType.message_created,
                    data={
                        "message": message_response.model_dump(),
                    },
                ),
            )
        )

        return message_response

    async def get_message(
        self, principal: auth.ActorPrincipal, conversation_id: uuid.UUID, message_id: uuid.UUID
    ) -> ConversationMessage:
        async with self._get_session() as session:
            message = (
                await session.exec(
                    query.select_conversation_messages_for(principal=principal)
                    .where(db.ConversationMessage.conversation_id == conversation_id)
                    .where(db.ConversationMessage.message_id == message_id)
                )
            ).one_or_none()
            if message is None:
                raise exceptions.NotFoundError()

        return convert.conversation_message_from_db(message)

    async def _add_user_participant(
        self, session: AsyncSession, user_principal: auth.UserPrincipal, conversation_id: uuid.UUID
    ) -> None:
        await user_.add_or_update_user_from(session=session, user_principal=user_principal)

        conversation = (
            await session.exec(select(db.Conversation).where(db.Conversation.conversation_id == conversation_id))
        ).one_or_none()
        if conversation is None:
            return

        await db.insert_if_not_exists(
            session,
            db.UserParticipant(
                conversation_id=conversation_id,
                user_id=user_principal.user_id,
                active_participant=True,
            ),
        )

        participant = (
            await session.exec(
                select(db.UserParticipant)
                .where(db.UserParticipant.conversation_id == conversation_id)
                .where(db.UserParticipant.user_id == user_principal.user_id)
                .with_for_update()
            )
        ).one()
        participant.active_participant = True
        session.add(participant)
        await session.commit()

    async def get_messages(
        self,
        principal: auth.ActorPrincipal,
        conversation_id: uuid.UUID,
        participant_roles: list[ParticipantRole] | None = None,
        participant_ids: list[str] | None = None,
        message_types: list[MessageType] | None = None,
        before: uuid.UUID | None = None,
        after: uuid.UUID | None = None,
        limit: int = 100,
    ) -> ConversationMessageList:
        async with self._get_session() as session:
            if isinstance(principal, auth.UserPrincipal):
                await self._add_user_participant(
                    user_principal=principal, conversation_id=conversation_id, session=session
                )

            conversation = (
                await session.exec(
                    query.select_conversations_for(principal=principal).where(
                        db.Conversation.conversation_id == conversation_id
                    )
                )
            ).one_or_none()
            if conversation is None:
                raise exceptions.NotFoundError()

            select_query = query.select_conversation_messages_for(principal=principal).where(
                db.ConversationMessage.conversation_id == conversation_id
            )

            if participant_roles is not None:
                select_query = select_query.where(
                    col(db.ConversationMessage.sender_participant_role).in_([r.value for r in participant_roles])
                )

            if participant_ids is not None:
                select_query = select_query.where(
                    col(db.ConversationMessage.sender_participant_id).in_(participant_ids)
                )

            if message_types is not None:
                select_query = select_query.where(
                    col(db.ConversationMessage.message_type).in_([t.value for t in message_types])
                )

            if before is not None:
                boundary = (
                    await session.exec(
                        query.select_conversation_messages_for(principal=principal).where(
                            db.ConversationMessage.message_id == before
                        )
                    )
                ).one_or_none()
                if boundary is not None:
                    select_query = select_query.where(db.ConversationMessage.sequence < boundary.sequence)

            if after is not None:
                boundary = (
                    await session.exec(
                        query.select_conversation_messages_for(principal=principal).where(
                            db.ConversationMessage.message_id == after
                        )
                    )
                ).one_or_none()
                if boundary is not None:
                    select_query = select_query.where(db.ConversationMessage.sequence > boundary.sequence)

            messages = list(
                (
                    await session.exec(select_query.order_by(col(db.ConversationMessage.sequence).desc()).limit(limit))
                ).all()
            )
            messages.reverse()

            return convert.conversation_message_list_from_db(messages)

    async def delete_message(
        self,
        conversation_id: uuid.UUID,
        message_id: uuid.UUID,
        principal: auth.ActorPrincipal,
    ) -> None:
        async with self._get_session() as session:
            message = (
                await session.exec(
                    query.select_conversation_messages_for(principal=principal)
                    .where(db.ConversationMessage.conversation_id == conversation_id)
                    .where(db.ConversationMessage.message_id == message_id)
                )
            ).one_or_none()
            if message is None:
                raise exceptions.NotFoundError()

            message_response = convert.conversation_message_from_db(message)

            await session.delete(message)
            await session.commit()

            await self._notify_event(
                ConversationEventQueueItem(
                    event=ConversationEvent(
                        conversation_id=conversation_id,
                        event=ConversationEventType.message_deleted,
                        data={
                            "message": message_response.model_dump(),
                        },
                    ),
                )
            )
