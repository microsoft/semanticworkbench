import datetime
from typing import AsyncContextManager, Awaitable, Callable, Iterable

import httpx
from semantic_workbench_api_model.assistant_model import ServiceInfoModel
from semantic_workbench_api_model.assistant_service_client import (
    AssistantServiceClientBuilder,
)
from semantic_workbench_api_model.workbench_model import (
    AssistantServiceRegistration,
    AssistantServiceRegistrationList,
    ConversationEventType,
    NewAssistantServiceRegistration,
    UpdateAssistantServiceRegistration,
    UpdateAssistantServiceRegistrationUrl,
)
from sqlalchemy import update
from sqlmodel import col, or_, select
from sqlmodel.ext.asyncio.session import AsyncSession

from .. import assistant_api_key, auth, db, settings
from ..event import ConversationEventQueueItem
from . import convert, exceptions
from . import participant as participant_
from . import user as user_


class AssistantServiceRegistrationController:

    def __init__(
        self,
        get_session: Callable[[], AsyncContextManager[AsyncSession]],
        notify_event: Callable[[ConversationEventQueueItem], Awaitable],
        api_key_store: assistant_api_key.ApiKeyStore,
        httpx_client_factory: Callable[[], httpx.AsyncClient],
    ) -> None:
        self._get_session = get_session
        self._notify_event = notify_event
        self._api_key_store = api_key_store
        self._httpx_client_factory = httpx_client_factory

    @property
    def _registration_is_secured(self) -> bool:
        return settings.service.assistant_api_key.is_secured

    async def api_key_source(self, assistant_service_id: str) -> str | None:
        generated_key_name = self._api_key_store.generate_key_name(assistant_service_id)
        if assistant_service_id == generated_key_name:
            return await self._api_key_store.get(generated_key_name)

        async with self._get_session() as session:
            api_key_name = (
                await session.exec(
                    select(db.AssistantServiceRegistration.api_key_name).where(
                        db.AssistantServiceRegistration.assistant_service_id == assistant_service_id
                    )
                )
            ).first()
        if api_key_name is None:
            return None
        return await self._api_key_store.get(api_key_name)

    async def _assistant_client_builder(
        self, registration: db.AssistantServiceRegistration
    ) -> AssistantServiceClientBuilder:
        return await assistant_service_client(
            registration=registration,
            api_key_store=self._api_key_store,
            httpx_client_factory=self._httpx_client_factory,
        )

    async def create_registration(
        self,
        user_principal: auth.UserPrincipal,
        new_assistant_service: NewAssistantServiceRegistration,
    ) -> AssistantServiceRegistration:
        async with self._get_session() as session:
            await user_.add_or_update_user_from(session=session, user_principal=user_principal)

            assistant_service_id = new_assistant_service.assistant_service_id.strip().lower()

            existing_registration = (
                await session.exec(
                    select(db.AssistantServiceRegistration).where(
                        db.AssistantServiceRegistration.assistant_service_id == assistant_service_id
                    )
                )
            ).first()
            if existing_registration is not None:
                raise exceptions.ConflictError("assistant service with this assistant_service_id already exists")

            api_key_name = self._api_key_store.generate_key_name(assistant_service_id)
            registration = db.AssistantServiceRegistration(
                assistant_service_id=assistant_service_id,
                created_by_user_id=user_principal.user_id,
                name=new_assistant_service.name,
                description=new_assistant_service.description,
                include_in_listing=new_assistant_service.include_in_listing,
                api_key_name=api_key_name,
            )
            session.add(registration)
            await session.flush()
            await session.refresh(registration)

            api_key = await self._api_key_store.reset(registration.api_key_name)

            await session.commit()

        return convert.assistant_service_registration_from_db(registration, api_key=api_key)

    async def get_registrations(
        self, user_ids: set[str], assistant_service_online: bool | None = None
    ) -> AssistantServiceRegistrationList:
        async with self._get_session() as session:
            query_registrations = (
                select(db.AssistantServiceRegistration)
                .where(col(db.AssistantServiceRegistration.include_in_listing).is_(True))
                .order_by(col(db.AssistantServiceRegistration.created_datetime).asc())
            )

            if user_ids:
                query_registrations = select(db.AssistantServiceRegistration).where(
                    col(db.AssistantServiceRegistration.created_by_user_id).in_(user_ids)
                )

            if assistant_service_online is not None:
                query_registrations = query_registrations.where(
                    col(db.AssistantServiceRegistration.assistant_service_online).is_(True)
                )

            assistant_services = await session.exec(query_registrations)

            return convert.assistant_service_registration_list_from_db(assistant_services)

    async def get_registration(self, assistant_service_id: str) -> AssistantServiceRegistration:
        async with self._get_session() as session:
            registration = (
                await session.exec(
                    select(db.AssistantServiceRegistration).where(
                        db.AssistantServiceRegistration.assistant_service_id == assistant_service_id
                    )
                )
            ).first()
            if registration is None:
                raise exceptions.NotFoundError()

            api_key = await self._api_key_store.get(registration.api_key_name)
            masked_api_key = self.mask_api_key(api_key)

            return convert.assistant_service_registration_from_db(registration, api_key=masked_api_key)

    @staticmethod
    def mask_api_key(api_key: str | None) -> str | None:
        if api_key is None:
            return None

        unmasked_length = 4
        if len(api_key) <= unmasked_length:
            # return a fixed mask if the api key is too short
            return "*" * 32

        # returns partially masked api key
        return f"{api_key[:unmasked_length]}{'*' * (len(api_key) - unmasked_length)}"

    async def update_registration(
        self,
        user_principal: auth.UserPrincipal,
        assistant_service_id: str,
        update_assistant_service: UpdateAssistantServiceRegistration,
    ) -> AssistantServiceRegistration:
        async with self._get_session() as session:
            registration_query = (
                select(db.AssistantServiceRegistration)
                .where(db.AssistantServiceRegistration.assistant_service_id == assistant_service_id)
                .with_for_update()
            )
            if self._registration_is_secured:
                registration_query = registration_query.where(
                    db.AssistantServiceRegistration.created_by_user_id == user_principal.user_id
                )
            registration = (await session.exec(registration_query)).first()

            if registration is None:
                raise exceptions.NotFoundError()

            if "name" in update_assistant_service.model_fields_set:
                if update_assistant_service.name is None:
                    raise exceptions.InvalidArgumentError("name cannot be null")
                registration.name = update_assistant_service.name
            if "description" in update_assistant_service.model_fields_set:
                if update_assistant_service.description is None:
                    raise exceptions.InvalidArgumentError("description cannot be null")
                registration.description = update_assistant_service.description
            if "include_in_listing" in update_assistant_service.model_fields_set:
                if update_assistant_service.include_in_listing is None:
                    raise exceptions.InvalidArgumentError("include_in_listing cannot be null")
                registration.include_in_listing = update_assistant_service.include_in_listing

            session.add(registration)
            await session.commit()
            await session.refresh(registration)

        return convert.assistant_service_registration_from_db(registration)

    async def update_assistant_service_url(
        self,
        assistant_service_principal: auth.AssistantServicePrincipal,
        assistant_service_id: str,
        update_assistant_service_url: UpdateAssistantServiceRegistrationUrl,
    ) -> tuple[AssistantServiceRegistration, Iterable]:
        if assistant_service_id != assistant_service_principal.assistant_service_id:
            raise exceptions.ForbiddenError()

        background_task_args: Iterable = ()
        async with self._get_session() as session:
            registration = (
                await session.exec(
                    select(db.AssistantServiceRegistration)
                    .where(db.AssistantServiceRegistration.assistant_service_id == assistant_service_id)
                    .with_for_update()
                )
            ).first()

            if registration is None:
                if self._registration_is_secured:
                    raise exceptions.NotFoundError()

                id = assistant_service_id.lower()
                api_key_name = self._api_key_store.generate_key_name(id)
                registration = db.AssistantServiceRegistration(
                    assistant_service_id=assistant_service_id,
                    created_by_user_id="semantic-workbench",
                    name=update_assistant_service_url.name,
                    description=update_assistant_service_url.description,
                    include_in_listing=True,
                    api_key_name=api_key_name,
                )

            if self._registration_is_secured and update_assistant_service_url.url.scheme != "https":
                raise exceptions.InvalidArgumentError("url must be https")

            registration.assistant_service_url = str(update_assistant_service_url.url)
            registration.assistant_service_online_expiration_datetime = datetime.datetime.now(
                datetime.UTC
            ) + datetime.timedelta(seconds=update_assistant_service_url.online_expires_in_seconds)

            if not registration.assistant_service_online:
                registration.assistant_service_online = True
                background_task_args = (self._update_participants, assistant_service_id)

            session.add(registration)
            await session.commit()
            await session.refresh(registration)

        return convert.assistant_service_registration_from_db(registration), background_task_args

    async def _update_participants(
        self,
        assistant_service_id: str,
    ) -> None:
        async with self._get_session() as session:
            participants_and_assistants = await session.exec(
                select(db.AssistantParticipant, db.Assistant)
                .join(db.Assistant, col(db.Assistant.assistant_id) == col(db.AssistantParticipant.assistant_id))
                .where(db.Assistant.assistant_service_id == assistant_service_id)
            )

            for participant, assistant in participants_and_assistants:
                participants = await participant_.get_conversation_participants(
                    session=session, conversation_id=participant.conversation_id, include_inactive=True
                )
                await self._notify_event(
                    ConversationEventQueueItem(
                        event=participant_.participant_event(
                            event_type=ConversationEventType.participant_updated,
                            conversation_id=participant.conversation_id,
                            participant=convert.conversation_participant_from_db_assistant(
                                participant, assistant=assistant
                            ),
                            participants=participants,
                        ),
                        # assistants do not need to receive assistant-participant online/offline events
                        event_audience={"user"},
                    )
                )

    async def reset_api_key(
        self,
        user_principal: auth.UserPrincipal,
        assistant_service_id: str,
    ) -> AssistantServiceRegistration:
        async with self._get_session() as session:
            registration_query = select(db.AssistantServiceRegistration).where(
                db.AssistantServiceRegistration.assistant_service_id == assistant_service_id
            )
            if self._registration_is_secured:
                registration_query = registration_query.where(
                    db.AssistantServiceRegistration.created_by_user_id == user_principal.user_id
                )

            registration = (await session.exec(registration_query)).first()
            if registration is None:
                raise exceptions.NotFoundError()

            api_key = await self._api_key_store.reset(registration.api_key_name)

        return convert.assistant_service_registration_from_db(registration, api_key=api_key)

    async def check_assistant_service_online_expired(self) -> None:
        async with self._get_session() as session:
            conn = await session.connection()
            result = await conn.execute(
                update(db.AssistantServiceRegistration)
                .where(col(db.AssistantServiceRegistration.assistant_service_online).is_(True))
                .where(
                    or_(
                        col(db.AssistantServiceRegistration.assistant_service_online_expiration_datetime).is_(None),
                        col(db.AssistantServiceRegistration.assistant_service_online_expiration_datetime)
                        <= datetime.datetime.now(
                            datetime.UTC,
                        ),
                    ),
                )
                .values(assistant_service_online=False)
                .returning(col(db.AssistantServiceRegistration.assistant_service_id))
            )
            if not result.rowcount:
                return

            assistant_service_ids = result.scalars().all()
            await session.commit()

        for assistant_service_id in assistant_service_ids:
            await self._update_participants(assistant_service_id=assistant_service_id)

    async def delete_registration(
        self,
        user_principal: auth.UserPrincipal,
        assistant_service_id: str,
    ) -> None:
        async with self._get_session() as session:
            registration = (
                await session.exec(
                    select(db.AssistantServiceRegistration)
                    .where(db.AssistantServiceRegistration.assistant_service_id == assistant_service_id)
                    .where(db.AssistantServiceRegistration.created_by_user_id == user_principal.user_id)
                )
            ).first()
            if registration is None:
                raise exceptions.NotFoundError()

            await session.delete(registration)
            await session.commit()

            await self._api_key_store.delete(registration.api_key_name)

    async def get_service_info(self, assistant_service_id: str) -> ServiceInfoModel:
        async with self._get_session() as session:
            registration = (
                await session.exec(
                    select(db.AssistantServiceRegistration).where(
                        db.AssistantServiceRegistration.assistant_service_id == assistant_service_id
                    )
                )
            ).first()

            if registration is None:
                raise exceptions.NotFoundError()

        return await (await self._assistant_client_builder(registration=registration)).for_service().get_service_info()


async def assistant_service_client(
    registration: db.AssistantServiceRegistration,
    api_key_store: assistant_api_key.ApiKeyStore,
    httpx_client_factory: Callable[[], httpx.AsyncClient],
) -> AssistantServiceClientBuilder:
    api_key = await api_key_store.get(registration.api_key_name)
    if api_key is None:
        raise RuntimeError(f"assistant service {registration.assistant_service_id} does not have API key set")

    return AssistantServiceClientBuilder(
        base_url=str(registration.assistant_service_url),
        api_key=api_key,
        httpx_client_factory=httpx_client_factory,
    )
