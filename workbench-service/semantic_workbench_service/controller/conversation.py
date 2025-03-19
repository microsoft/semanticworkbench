import datetime
import logging
import openai_client
import uuid
from typing import Annotated, AsyncContextManager, Awaitable, Callable, Iterable, Literal, Sequence

import deepmerge
from pydantic import BaseModel, Field, HttpUrl
from semantic_workbench_api_model.assistant_service_client import AssistantError
from semantic_workbench_api_model.workbench_model import (
    Conversation,
    ConversationEvent,
    ConversationEventType,
    ConversationList,
    ConversationMessage,
    ConversationMessageDebug,
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
from sqlmodel import and_, col, or_, select
from sqlmodel.ext.asyncio.session import AsyncSession

from .. import auth, db, query, settings
from ..event import ConversationEventQueueItem
from . import assistant, convert, exceptions
from . import participant as participant_
from . import user as user_

logger = logging.getLogger(__name__)


class ConversationTitleResponse(BaseModel):
    """Model for responses from LLM for automatic conversation re-titling."""

    title: Annotated[
        str,
        Field(
            description="The updated title of the conversation. If the subject matter of the conversation has changed significantly from the current title, suggest a short, but descriptive title for the conversation. Ideally 4 words or less in length. Leave it blank to keep the current title.",
        ),
    ]


META_DATA_KEY_USER_SET_TITLE = "__user_set_title"
META_DATA_KEY_AUTO_TITLE_COUNT = "__auto_title_count"
AUTO_TITLE_COUNT_LIMIT = 3
"""
The maximum number of times a conversation can be automatically retitled.
"""


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

    async def create_conversation(
        self,
        new_conversation: NewConversation,
        user_principal: auth.UserPrincipal,
    ) -> Conversation:
        async with self._get_session() as session:
            await user_.add_or_update_user_from(session=session, user_principal=user_principal)

            conversation = db.Conversation(
                owner_id=user_principal.user_id,
                title=new_conversation.title or NewConversation().title,
                meta_data=new_conversation.metadata,
                imported_from_conversation_id=None,
            )

            if new_conversation.title and new_conversation.title != NewConversation().title:
                conversation.meta_data = {
                    **conversation.meta_data,
                    META_DATA_KEY_USER_SET_TITLE: True,
                }

            session.add(conversation)

            session.add(
                db.UserParticipant(
                    conversation_id=conversation.conversation_id,
                    user_id=user_principal.user_id,
                    conversation_permission="read_write",
                )
            )

            await session.commit()
            await session.refresh(conversation)

        return await self.get_conversation(
            conversation_id=conversation.conversation_id, principal=user_principal, latest_message_types=set()
        )

    async def _projections_with_participants(
        self,
        session: AsyncSession,
        conversation_projections: Sequence[tuple[db.Conversation, db.ConversationMessage | None, bool, str]],
    ) -> Iterable[
        tuple[
            db.Conversation,
            Iterable[db.UserParticipant],
            Iterable[db.AssistantParticipant],
            dict[uuid.UUID, db.Assistant],
            db.ConversationMessage | None,
            bool,
            str,
        ]
    ]:
        user_participants = (
            await session.exec(
                select(db.UserParticipant).where(
                    col(db.UserParticipant.conversation_id).in_([
                        c[0].conversation_id for c in conversation_projections
                    ])
                )
            )
        ).all()

        assistant_participants = (
            await session.exec(
                select(db.AssistantParticipant).where(
                    col(db.AssistantParticipant.conversation_id).in_([
                        c[0].conversation_id for c in conversation_projections
                    ])
                )
            )
        ).all()

        assistants = (
            await session.exec(
                select(db.Assistant).where(
                    col(db.Assistant.assistant_id).in_([p.assistant_id for p in assistant_participants])
                )
            )
        ).all()
        assistants_map = {assistant.assistant_id: assistant for assistant in assistants}

        def merge() -> Iterable[
            tuple[
                db.Conversation,
                Iterable[db.UserParticipant],
                Iterable[db.AssistantParticipant],
                dict[uuid.UUID, db.Assistant],
                db.ConversationMessage | None,
                bool,
                str,
            ]
        ]:
            for conversation, latest_message, latest_message_has_debug, permission in conversation_projections:
                conversation_id = conversation.conversation_id
                conversation_user_participants = (
                    up for up in user_participants if up.conversation_id == conversation_id
                )
                conversation_assistant_participants = (
                    ap for ap in assistant_participants if ap.conversation_id == conversation_id
                )
                yield (
                    conversation,
                    conversation_user_participants,
                    conversation_assistant_participants,
                    assistants_map,
                    latest_message,
                    latest_message_has_debug,
                    permission,
                )

        return merge()

    async def get_conversations(
        self,
        principal: auth.ActorPrincipal,
        latest_message_types: set[MessageType],
        include_all_owned: bool = False,
    ) -> ConversationList:
        async with self._get_session() as session:
            include_all_owned = include_all_owned and isinstance(principal, auth.UserPrincipal)

            conversation_projections = (
                await session.exec(
                    query.select_conversation_projections_for(
                        principal=principal,
                        include_all_owned=include_all_owned,
                        include_observer=True,
                        latest_message_types=latest_message_types,
                    ).order_by(col(db.Conversation.created_datetime).desc())
                )
            ).all()

            projections_with_participants = await self._projections_with_participants(
                session=session, conversation_projections=conversation_projections
            )

            return convert.conversation_list_from_db(models=projections_with_participants)

    async def get_assistant_conversations(
        self,
        user_principal: auth.UserPrincipal,
        assistant_id: uuid.UUID,
        latest_message_types: set[MessageType],
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

            conversation_projections = (
                await session.exec(
                    query.select_conversation_projections_for(
                        principal=auth.AssistantPrincipal(
                            assistant_service_id=assistant.assistant_service_id, assistant_id=assistant_id
                        ),
                        latest_message_types=latest_message_types,
                    )
                )
            ).all()

            projections_with_participants = await self._projections_with_participants(
                session=session, conversation_projections=conversation_projections
            )

            return convert.conversation_list_from_db(models=projections_with_participants)

    async def get_conversation(
        self,
        conversation_id: uuid.UUID,
        principal: auth.ActorPrincipal,
        latest_message_types: set[MessageType],
    ) -> Conversation:
        async with self._get_session() as session:
            include_all_owned = isinstance(principal, auth.UserPrincipal)

            conversation_projection = (
                await session.exec(
                    query.select_conversation_projections_for(
                        principal=principal,
                        include_all_owned=include_all_owned,
                        include_observer=True,
                        latest_message_types=latest_message_types,
                    ).where(db.Conversation.conversation_id == conversation_id)
                )
            ).one_or_none()
            if conversation_projection is None:
                raise exceptions.NotFoundError()

            projections_with_participants = await self._projections_with_participants(
                session=session,
                conversation_projections=[conversation_projection],
            )

            (
                conversation,
                user_participants,
                assistant_participants,
                assistants,
                latest_message,
                latest_message_has_debug,
                permission,
            ) = next(iter(projections_with_participants))

            return convert.conversation_from_db(
                model=conversation,
                latest_message=latest_message,
                latest_message_has_debug=latest_message_has_debug,
                permission=permission,
                user_participants=user_participants,
                assistant_participants=assistant_participants,
                assistants=assistants,
            )

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
                        include_all_owned=True,
                    )
                    .where(
                        db.Conversation.conversation_id == conversation_id,
                        db.Conversation.owner_id == user_principal.user_id,
                    )
                    .with_for_update()
                )
            ).one_or_none()
            if conversation is None:
                raise exceptions.NotFoundError()

            for key, value in update_conversation.model_dump(exclude_unset=True).items():
                match key:
                    case "metadata":
                        system_entries = {k: v for k, v in conversation.meta_data.items() if k.startswith("__")}
                        conversation.meta_data = {**value, **system_entries}
                    case "title":
                        if value == conversation.title:
                            continue
                        conversation.title = value
                        conversation.meta_data = {
                            **conversation.meta_data,
                            META_DATA_KEY_USER_SET_TITLE: True,
                        }
                    case _:
                        setattr(conversation, key, value)

            session.add(conversation)
            await session.commit()
            await session.refresh(conversation)

        conversation_model = await self.get_conversation(
            conversation_id=conversation.conversation_id, principal=user_principal, latest_message_types=set()
        )

        await self._notify_event(
            ConversationEventQueueItem(
                event=ConversationEvent(
                    conversation_id=conversation.conversation_id,
                    event=ConversationEventType.conversation_updated,
                    data={
                        "conversation": conversation_model.model_dump(),
                    },
                )
            )
        )

        return conversation_model

    async def get_conversation_participants(
        self,
        conversation_id: uuid.UUID,
        principal: auth.ActorPrincipal,
        include_inactive: bool = False,
    ) -> ConversationParticipantList:
        async with self._get_session() as session:
            conversation = (
                await session.exec(
                    query.select_conversations_for(
                        principal=principal, include_all_owned=True, include_observer=True
                    ).where(db.Conversation.conversation_id == conversation_id)
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
                    query.select_conversations_for(
                        principal=principal, include_all_owned=True, include_observer=True
                    ).where(db.Conversation.conversation_id == conversation_id)
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

        async with self._get_session() as session:

            async def update_user_participant(
                conversation: db.Conversation, user: db.User
            ) -> tuple[
                ConversationParticipant,
                Literal[ConversationEventType.participant_updated,] | None,
            ]:
                event_type: ConversationEventType | None = None
                participant = (
                    await session.exec(
                        select(db.UserParticipant)
                        .join(db.Conversation)
                        .where(db.UserParticipant.conversation_id == conversation.conversation_id)
                        .where(db.UserParticipant.user_id == user.user_id)
                        .where(
                            or_(
                                col(db.UserParticipant.active_participant).is_(True),
                                db.Conversation.owner_id == user.user_id,
                            )
                        )
                        .with_for_update()
                    )
                ).one_or_none()
                if participant is None:
                    raise exceptions.NotFoundError()

                if update_participant.active_participant is not None:
                    event_type = ConversationEventType.participant_updated
                    participant.active_participant = update_participant.active_participant

                if update_participant.status != participant.status:
                    event_type = event_type or ConversationEventType.participant_updated
                    participant.status = update_participant.status
                    participant.status_updated_datetime = datetime.datetime.now(datetime.UTC)

                if update_participant.metadata is not None:
                    event_type = event_type or ConversationEventType.participant_updated
                    participant.meta_data = deepmerge.always_merger.merge(
                        participant.meta_data or {}, update_participant.metadata
                    )

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

                if update_participant.metadata is not None:
                    event_type = event_type or ConversationEventType.participant_updated
                    participant.meta_data = deepmerge.always_merger.merge(
                        participant.meta_data or {}, update_participant.metadata
                    )

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
                    await user_.add_or_update_user_from(user_principal=principal, session=session)

                    # users can update participants in any conversation they own or are participants of
                    conversation = (
                        await session.exec(
                            query.select_conversations_for(
                                principal=principal, include_all_owned=True, include_observer=True
                            ).where(db.Conversation.conversation_id == conversation_id)
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
                            # users can only update their own participant
                            if participant_id != principal.user_id:
                                raise exceptions.ForbiddenError()

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
    ) -> tuple[ConversationMessage, Iterable]:
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
                        query.select(db.ConversationMessage)
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
                    # allow assistants to send messages as users, if provided
                    if new_message.sender is not None and new_message.sender.participant_role == "user":
                        role = "user"
                        participant_id = new_message.sender.participant_id
                    else:
                        role = "assistant"
                        participant_id = str(principal.assistant_id)

            # pop "debug" from metadata, if it exists, and merge with the debug field
            message_debug = (new_message.metadata or {}).pop("debug", None)
            # ensure that message_debug is a dictionary, in cases like {"debug": "some message"}, or {"debug": [1,2]}
            if message_debug and not isinstance(message_debug, dict):
                message_debug = {"debug": message_debug}
            message_debug = deepmerge.always_merger.merge(message_debug or {}, new_message.debug_data or {})

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

            if message_debug:
                debug = db.ConversationMessageDebug(
                    message_id=message.message_id,
                    data=message_debug,
                )
                session.add(debug)

            await session.commit()
            await session.refresh(message)

            background_task: Iterable = ()
            if self._conversation_candidate_for_retitling(
                conversation=conversation
            ) and self._message_candidate_for_retitling(message=message):
                background_task = (
                    self._retitle_conversation,
                    principal,
                    conversation_id,
                )

        message_response = convert.conversation_message_from_db(message, has_debug=bool(message_debug))

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

        return message_response, background_task

    def _message_candidate_for_retitling(self, message: db.ConversationMessage) -> bool:
        """Check if the message is a candidate for retitling the conversation."""
        if message.sender_participant_role != ParticipantRole.user.value:
            return False

        if message.message_type != MessageType.chat.value:
            return False

        return True

    def _conversation_candidate_for_retitling(self, conversation: db.Conversation) -> bool:
        """Check if the conversation is a candidate for retitling."""
        if conversation.meta_data.get(META_DATA_KEY_USER_SET_TITLE, False):
            return False

        if conversation.meta_data.get(META_DATA_KEY_AUTO_TITLE_COUNT, 0) >= AUTO_TITLE_COUNT_LIMIT:
            return False

        return True

    async def _retitle_conversation(self, principal: auth.ActorPrincipal, conversation_id: uuid.UUID) -> None:
        """Retitle the conversation based on the most recent messages."""

        if not settings.service.azure_openai_endpoint:
            logger.warning(
                "Azure OpenAI endpoint is not configured, skipping retitling conversation %s", conversation_id
            )
            return

        if not settings.service.azure_openai_deployment:
            logger.warning(
                "Azure OpenAI deployment is not configured, skipping retitling conversation %s", conversation_id
            )
            return

        async with self._get_session() as session:
            # Retrieve the most recent messages
            messages = list(
                (
                    await session.exec(
                        select(db.ConversationMessage)
                        .where(
                            db.ConversationMessage.conversation_id == conversation_id,
                            db.ConversationMessage.sender_participant_role == ParticipantRole.user.value,
                            db.ConversationMessage.message_type == MessageType.chat.value,
                        )
                        .order_by(col(db.ConversationMessage.sequence).desc())
                        .limit(10)
                    )
                ).all()
            )
            if not messages:
                return

            messages.reverse()

        # Call the LLM to get a new title
        try:
            async with openai_client.create_client(
                openai_client.AzureOpenAIServiceConfig(
                    auth_config=openai_client.AzureOpenAIAzureIdentityAuthConfig(),
                    azure_openai_deployment=settings.service.azure_openai_deployment,
                    azure_openai_endpoint=HttpUrl(settings.service.azure_openai_endpoint),
                ),
            ) as client:
                response = await client.beta.chat.completions.parse(
                    messages=[
                        *[
                            {
                                "role": "user",
                                "content": message.content,
                            }
                            for message in messages
                        ],
                        {
                            "role": "developer",
                            "content": ("The current conversation title is: {conversation.title}"),
                        },
                    ],
                    model=settings.service.azure_openai_model,
                    # the model's description also contains instructions
                    response_format=ConversationTitleResponse,
                )

                if not response.choices:
                    raise RuntimeError("No choices in azure openai response")

                result = response.choices[0].message.parsed
                if result is None:
                    raise RuntimeError("No parsed result in azure openai response")

        except Exception:
            logger.exception("Failed to retitle conversation %s", conversation_id)
            return

        # Update the conversation title if it has not already been changed from the default
        async with self._get_session() as session:
            conversation = (
                await session.exec(
                    select(db.Conversation).where(db.Conversation.conversation_id == conversation_id).with_for_update()
                )
            ).one_or_none()
            if conversation is None:
                return

            if not self._conversation_candidate_for_retitling(conversation):
                return

            if result.title.strip():
                conversation.title = result.title.strip()

            conversation.meta_data = {
                **conversation.meta_data,
                META_DATA_KEY_AUTO_TITLE_COUNT: conversation.meta_data.get(META_DATA_KEY_AUTO_TITLE_COUNT, 0) + 1,
            }

            session.add(conversation)
            await session.commit()
            await session.refresh(conversation)

        conversation_model = await self.get_conversation(
            conversation_id=conversation.conversation_id,
            principal=principal,
            latest_message_types=set(),
        )

        await self._notify_event(
            ConversationEventQueueItem(
                event=ConversationEvent(
                    conversation_id=conversation.conversation_id,
                    event=ConversationEventType.conversation_updated,
                    data={
                        "conversation": conversation_model.model_dump(),
                    },
                )
            )
        )

    async def get_message(
        self, principal: auth.ActorPrincipal, conversation_id: uuid.UUID, message_id: uuid.UUID
    ) -> ConversationMessage:
        async with self._get_session() as session:
            projection = (
                await session.exec(
                    query.select_conversation_message_projections_for(principal=principal)
                    .where(db.ConversationMessage.conversation_id == conversation_id)
                    .where(db.ConversationMessage.message_id == message_id)
                )
            ).one_or_none()
            if projection is None:
                raise exceptions.NotFoundError()

        message, has_debug = projection

        return convert.conversation_message_from_db(message, has_debug=has_debug)

    async def get_message_debug(
        self, principal: auth.ActorPrincipal, conversation_id: uuid.UUID, message_id: uuid.UUID
    ) -> ConversationMessageDebug:
        async with self._get_session() as session:
            message_debug = (
                await session.exec(
                    query.select_conversation_message_debugs_for(principal=principal).where(
                        db.Conversation.conversation_id == conversation_id,
                        db.ConversationMessageDebug.message_id == message_id,
                    )
                )
            ).one_or_none()
            if message_debug is None:
                raise exceptions.NotFoundError()

        return convert.conversation_message_debug_from_db(message_debug)

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
            conversation = (
                await session.exec(
                    query.select_conversations_for(principal=principal, include_observer=True).where(
                        db.Conversation.conversation_id == conversation_id
                    )
                )
            ).one_or_none()
            if conversation is None:
                raise exceptions.NotFoundError()

            select_query = query.select_conversation_message_projections_for(principal=principal).where(
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
        user_principal: auth.UserPrincipal,
    ) -> None:
        async with self._get_session() as session:
            message = (
                await session.exec(
                    query.select_conversation_messages_for(principal=user_principal).where(
                        db.ConversationMessage.conversation_id == conversation_id,
                        db.ConversationMessage.message_id == message_id,
                        or_(
                            db.Conversation.owner_id == user_principal.user_id,
                            db.ConversationMessage.sender_participant_id == user_principal.user_id,
                            and_(
                                col(db.UserParticipant.active_participant).is_(True),
                                db.UserParticipant.conversation_permission == "read_write",
                            ),
                        ),
                    )
                )
            ).one_or_none()
            if message is None:
                raise exceptions.NotFoundError()

            message_response = convert.conversation_message_from_db(message, has_debug=False)

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
