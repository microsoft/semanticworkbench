import asyncio
import datetime
import logging
import os
import re
import tempfile
import uuid
import zipfile
from typing import IO, AsyncContextManager, Awaitable, BinaryIO, Callable, NamedTuple

import httpx
from semantic_workbench_api_model.assistant_model import (
    AssistantPutRequestModel,
    ConfigPutRequestModel,
    ConfigResponseModel,
    ConversationPutRequestModel,
    StateDescriptionListResponseModel,
    StatePutRequestModel,
    StateResponseModel,
)
from semantic_workbench_api_model.assistant_service_client import (
    AssistantError,
    AssistantServiceClientBuilder,
)
from semantic_workbench_api_model.workbench_model import (
    Assistant,
    AssistantList,
    AssistantStateEvent,
    ConversationEvent,
    ConversationEventType,
    ConversationImportResult,
    NewAssistant,
    UpdateAssistant,
)
from sqlmodel import col, select
from sqlmodel.ext.asyncio.session import AsyncSession

from .. import assistant_api_key, auth, db, query
from ..event import ConversationEventQueueItem
from . import convert, exceptions, export_import
from . import participant as participant_
from . import user as user_
from .assistant_service_registration import assistant_service_client

logger = logging.getLogger(__name__)


ExportResult = NamedTuple(
    "ExportResult",
    [("file_path", str), ("content_type", str), ("filename", str), ("cleanup", Callable[[], None])],
)


class AssistantController:
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

    async def _assistant_client_builder(
        self, registration: db.AssistantServiceRegistration
    ) -> AssistantServiceClientBuilder:
        return await assistant_service_client(
            registration=registration,
            api_key_store=self._api_key_store,
            httpx_client_factory=self._httpx_client_factory,
        )

    async def _ensure_assistant(
        self,
        session: AsyncSession,
        assistant_id: uuid.UUID,
    ) -> db.Assistant:
        assistant = (
            await session.exec(
                query.select(
                    db.Assistant,
                ).where(db.Assistant.assistant_id == assistant_id)
            )
        ).one_or_none()
        if assistant is None:
            raise exceptions.NotFoundError()

        return assistant

    async def _ensure_assistant_conversation(
        self, session: AsyncSession, assistant: db.Assistant, conversation_id: uuid.UUID
    ) -> db.Conversation:
        conversation = (
            await session.exec(
                query.select_conversations_for(
                    principal=auth.AssistantPrincipal(
                        assistant_service_id=assistant.assistant_service_id, assistant_id=assistant.assistant_id
                    )
                ).where(db.Conversation.conversation_id == conversation_id)
            )
        ).one_or_none()
        if conversation is None:
            raise exceptions.NotFoundError()

        return conversation

    async def _put_assistant(self, assistant: db.Assistant, from_export: IO[bytes] | None) -> None:
        await (
            await self._assistant_client_builder(
                registration=assistant.related_assistant_service_registration,
            )
        ).for_service().put_assistant_instance(
            assistant_id=assistant.assistant_id,
            request=AssistantPutRequestModel(assistant_name=assistant.name),
            from_export=from_export,
        )

    async def _forward_event_to_assistant(self, assistant: db.Assistant, event: ConversationEvent) -> None:
        if not assistant.related_assistant_service_registration.assistant_service_online:
            logger.error(
                "cannot forward event to offline assistant; assistant_id: %s, assistant_service_id: %s",
                assistant.assistant_id,
                assistant.assistant_service_id,
            )
            return

        logger.debug(
            "forwarding event to assistant; assistant_id: %s, conversation_id: %s, id: %s",
            assistant.assistant_id,
            event.conversation_id,
            event.id,
        )
        try:
            await (
                await self._assistant_client_builder(
                    registration=assistant.related_assistant_service_registration,
                )
            ).for_assistant_instance(assistant_id=assistant.assistant_id).post_conversation_event(event=event)
        except AssistantError:
            logger.error(
                "error forwarding event to assistant; assistant_id: %s, conversation_id: %s, event: %s",
                assistant.assistant_id,
                event.conversation_id,
                event,
                exc_info=True,
            )
        logger.debug(
            "forwarded event to assistant; assistant_id: %s, conversation_id: %s, id: %s",
            assistant.assistant_id,
            event.conversation_id,
            event.id,
        )

    async def _disconnect_assistant(self, assistant: db.Assistant) -> None:
        await (
            await self._assistant_client_builder(
                registration=assistant.related_assistant_service_registration,
            )
        ).for_service().delete_assistant_instance(assistant_id=assistant.assistant_id)

    async def _remove_assistant_from_conversation(
        self,
        session: AsyncSession,
        assistant: db.Assistant,
        conversation_id: uuid.UUID,
    ):
        try:
            await self.disconnect_assistant_from_conversation(conversation_id=conversation_id, assistant=assistant)
        except AssistantError:
            logger.error("error disconnecting assistant", exc_info=True)

        for participant in await session.exec(
            select(db.AssistantParticipant)
            .where(
                db.AssistantParticipant.conversation_id == conversation_id,
                db.AssistantParticipant.assistant_id == assistant.assistant_id,
            )
            .with_for_update()
        ):
            participant.active_participant = False
            session.add(participant)

            participants = await participant_.get_conversation_participants(
                session=session, conversation_id=conversation_id, include_inactive=True
            )
            await self._notify_event(
                ConversationEventQueueItem(
                    event=participant_.participant_event(
                        event_type=ConversationEventType.participant_deleted,
                        conversation_id=conversation_id,
                        participant=convert.conversation_participant_from_db_assistant(
                            participant, assistant=assistant
                        ),
                        participants=participants,
                    )
                )
            )

        await session.flush()

    async def disconnect_assistant_from_conversation(self, conversation_id: uuid.UUID, assistant: db.Assistant) -> None:
        await (
            await self._assistant_client_builder(
                registration=assistant.related_assistant_service_registration,
            )
        ).for_assistant_instance(assistant_id=assistant.assistant_id).delete_conversation(
            conversation_id=conversation_id
        )

    async def connect_assistant_to_conversation(
        self, conversation: db.Conversation, assistant: db.Assistant, from_export: IO[bytes] | None
    ) -> None:
        await (
            await self._assistant_client_builder(
                registration=assistant.related_assistant_service_registration,
            )
        ).for_assistant_instance(assistant_id=assistant.assistant_id).put_conversation(
            ConversationPutRequestModel(id=str(conversation.conversation_id), title=conversation.title),
            from_export=from_export,
        )

    async def forward_event_to_assistants(self, event: ConversationEvent) -> None:
        async with self._get_session() as session:
            assistants = (
                await session.exec(
                    select(db.Assistant)
                    .join(
                        db.AssistantParticipant,
                        col(db.Assistant.assistant_id) == col(db.AssistantParticipant.assistant_id),
                    )
                    .join(db.AssistantServiceRegistration)
                    .where(col(db.AssistantServiceRegistration.assistant_service_online).is_(True))
                    .where(col(db.AssistantParticipant.active_participant).is_(True))
                    .where(db.AssistantParticipant.conversation_id == event.conversation_id)
                )
            ).all()

        async with asyncio.TaskGroup() as task_group:
            for assistant in assistants:
                task_group.create_task(self._forward_event_to_assistant(assistant=assistant, event=event))

    async def create_assistant(
        self,
        new_assistant: NewAssistant,
        user_principal: auth.UserPrincipal,
    ) -> Assistant:
        async with self._get_session() as session:
            await user_.add_or_update_user_from(session=session, user_principal=user_principal)

            assistant_service = (
                await session.exec(
                    select(db.AssistantServiceRegistration).where(
                        db.AssistantServiceRegistration.assistant_service_id == new_assistant.assistant_service_id
                    )
                )
            ).one_or_none()
            if assistant_service is None:
                raise exceptions.InvalidArgumentError(
                    detail=f"assistant service id {new_assistant.assistant_service_id} is not valid"
                )

            if not assistant_service.assistant_service_online:
                raise exceptions.InvalidArgumentError(
                    detail=(
                        f"assistant service '{assistant_service.name}' ({assistant_service.assistant_service_id}) is"
                        " currently offline"
                    )
                )

            assistant = db.Assistant(
                owner_id=user_principal.user_id,
                name=new_assistant.name,
                image=new_assistant.image,
                meta_data=new_assistant.metadata,
                assistant_service_id=assistant_service.assistant_service_id,
            )
            session.add(assistant)
            await session.commit()
            await session.refresh(assistant)

            try:
                await self._put_assistant(assistant=assistant, from_export=None)
            except AssistantError:
                logger.error("error creating assistant", exc_info=True)
                await session.delete(assistant)
                await session.commit()
                raise

        return await self.get_assistant(assistant_id=assistant.assistant_id)

    async def update_assistant(
        self,
        assistant_id: uuid.UUID,
        update_assistant: UpdateAssistant,
    ) -> Assistant:
        async with self._get_session() as session:
            assistant = (
                await session.exec(
                    query.select(
                        db.Assistant,
                    )
                    .where(db.Assistant.assistant_id == assistant_id)
                    .with_for_update()
                )
            ).one_or_none()
            if assistant is None:
                raise exceptions.NotFoundError()

            assistant_service = (
                await session.exec(
                    select(db.AssistantServiceRegistration).where(
                        db.AssistantServiceRegistration.assistant_service_id == assistant.assistant_service_id
                    )
                )
            ).one()
            if not assistant_service.assistant_service_online:
                raise exceptions.InvalidArgumentError(
                    detail=f"assistant service '{assistant_service.name}' is currently offline"
                )

            updates = update_assistant.model_dump(exclude_unset=True)
            for field, value in updates.items():
                match field:
                    case "metadata":
                        assistant.meta_data = value
                    case _:
                        setattr(assistant, field, value)

            session.add(assistant)

            try:
                await self._put_assistant(assistant=assistant, from_export=None)
            except AssistantError:
                logger.error("error updating assistant", exc_info=True)
                raise

            await session.commit()
            await session.refresh(assistant)

        return await self.get_assistant(assistant_id=assistant.assistant_id)

    async def delete_assistant(
        self,
        assistant_id: uuid.UUID,
    ) -> None:
        async with self._get_session() as session:
            assistant = (
                await session.exec(
                    query.select(
                        db.Assistant,
                    )
                    .where(db.Assistant.assistant_id == assistant_id)
                    .with_for_update()
                )
            ).one_or_none()
            if assistant is None:
                raise exceptions.NotFoundError()

            conversations = (
                await session.exec(
                    select(db.Conversation)
                    .join(db.AssistantParticipant)
                    .where(db.AssistantParticipant.assistant_id == assistant_id)
                )
            ).all()

            for conversation in conversations:
                await self._remove_assistant_from_conversation(
                    session=session,
                    assistant=assistant,
                    conversation_id=conversation.conversation_id,
                )

            try:
                await self._disconnect_assistant(assistant=assistant)

            except AssistantError:
                logger.error("error disconnecting assistant", exc_info=True)

            await session.delete(assistant)
            await session.commit()

    async def get_assistants(
        self,
        user_principal: auth.UserPrincipal,
    ) -> AssistantList:
        async with self._get_session() as session:
            assistants = await session.exec(
                query.select_assistants_for(user_principal=user_principal).order_by(
                    col(db.Assistant.created_datetime).desc(),
                    col(db.Assistant.name).asc(),
                )
            )

            return convert.assistant_list_from_db(models=assistants)

    async def get_assistant(
        self,
        assistant_id: uuid.UUID,
    ) -> Assistant:
        async with self._get_session() as session:
            assistant = await self._ensure_assistant(
                assistant_id=assistant_id,
                session=session,
            )
            return convert.assistant_from_db(model=assistant)

    async def get_assistant_config(
        self,
        assistant_id: uuid.UUID,
    ) -> ConfigResponseModel:
        async with self._get_session() as session:
            assistant = await self._ensure_assistant(assistant_id=assistant_id, session=session)

        return (
            await (
                await self._assistant_client_builder(
                    registration=assistant.related_assistant_service_registration,
                )
            )
            .for_assistant_instance(assistant_id=assistant.assistant_id)
            .get_config()
        )

    async def update_assistant_config(
        self,
        assistant_id: uuid.UUID,
        updated_config: ConfigPutRequestModel,
    ) -> ConfigResponseModel:
        async with self._get_session() as session:
            assistant = await self._ensure_assistant(assistant_id=assistant_id, session=session)

        return (
            await (
                await self._assistant_client_builder(
                    registration=assistant.related_assistant_service_registration,
                )
            )
            .for_assistant_instance(assistant_id=assistant.assistant_id)
            .put_config(updated_config)
        )

    async def get_assistant_conversation_state_descriptions(
        self,
        assistant_id: uuid.UUID,
        conversation_id: uuid.UUID,
    ) -> StateDescriptionListResponseModel:
        async with self._get_session() as session:
            assistant = await self._ensure_assistant(assistant_id=assistant_id, session=session)
            await self._ensure_assistant_conversation(
                assistant=assistant, conversation_id=conversation_id, session=session
            )

        return (
            await (
                await self._assistant_client_builder(
                    registration=assistant.related_assistant_service_registration,
                )
            )
            .for_assistant_instance(assistant_id=assistant.assistant_id)
            .get_state_descriptions(conversation_id=conversation_id)
        )

    async def get_assistant_conversation_state(
        self,
        assistant_id: uuid.UUID,
        conversation_id: uuid.UUID,
        state_id: str,
    ) -> StateResponseModel:
        async with self._get_session() as session:
            assistant = await self._ensure_assistant(assistant_id=assistant_id, session=session)
            await self._ensure_assistant_conversation(
                assistant=assistant, conversation_id=conversation_id, session=session
            )

        return (
            await (
                await self._assistant_client_builder(
                    registration=assistant.related_assistant_service_registration,
                )
            )
            .for_assistant_instance(assistant_id=assistant.assistant_id)
            .get_state(conversation_id=conversation_id, state_id=state_id)
        )

    async def update_assistant_conversation_state(
        self,
        assistant_id: uuid.UUID,
        conversation_id: uuid.UUID,
        state_id: str,
        updated_state: StatePutRequestModel,
    ) -> StateResponseModel:
        async with self._get_session() as session:
            assistant = await self._ensure_assistant(assistant_id=assistant_id, session=session)
            await self._ensure_assistant_conversation(
                assistant=assistant, conversation_id=conversation_id, session=session
            )

        return (
            await (
                await self._assistant_client_builder(
                    registration=assistant.related_assistant_service_registration,
                )
            )
            .for_assistant_instance(assistant_id=assistant.assistant_id)
            .put_state(conversation_id=conversation_id, state_id=state_id, updated_state=updated_state)
        )

    async def post_assistant_state_event(
        self,
        assistant_id: uuid.UUID,
        state_event: AssistantStateEvent,
        assistant_principal: auth.AssistantServicePrincipal,
        conversation_ids: list[uuid.UUID] = [],
    ) -> None:
        async with self._get_session() as session:
            assistant = await self._ensure_assistant(assistant_id=assistant_id, session=session)
            if assistant_principal.assistant_service_id != assistant.assistant_service_id:
                raise exceptions.ForbiddenError()

            if not conversation_ids:
                for participant in await session.exec(
                    select(db.AssistantParticipant).where(db.AssistantParticipant.assistant_id == assistant_id)
                ):
                    conversation_ids.append(participant.conversation_id)

        match state_event.event:
            case "focus":
                conversation_event_type = ConversationEventType.assistant_state_focus
            case "created":
                conversation_event_type = ConversationEventType.assistant_state_created
            case "deleted":
                conversation_event_type = ConversationEventType.assistant_state_deleted
            case _:
                conversation_event_type = ConversationEventType.assistant_state_updated

        for conversation_id in conversation_ids:
            await self._notify_event(
                ConversationEventQueueItem(
                    event=ConversationEvent(
                        conversation_id=conversation_id,
                        event=conversation_event_type,
                        data={
                            "assistant_id": assistant_id,
                            "state_id": state_event.state_id,
                            "conversation_id": conversation_id,
                        },
                    ),
                )
            )

    EXPORT_WORKBENCH_FILENAME = "workbench.jsonl"
    EXPORT_ASSISTANT_DATA_FILENAME = "assistant_data.bin"
    EXPORT_ASSISTANT_CONVERSATION_DATA_FILENAME = "conversation_data.bin"

    async def export_assistant(
        self,
        assistant_id: uuid.UUID,
    ) -> ExportResult:
        async with self._get_session() as session:
            assistant = await self._ensure_assistant(assistant_id=assistant_id, session=session)

            conversation = (
                await session.exec(
                    select(db.Conversation)
                    .join(db.AssistantParticipant)
                    .where(db.AssistantParticipant.assistant_id == assistant.assistant_id)
                    .order_by(col(db.AssistantParticipant.joined_datetime).desc())
                )
            ).first()
            if conversation is None:
                raise exceptions.NotFoundError(detail="conversation not found for assistant")

            messages = await session.exec(
                select(db.ConversationMessage)
                .where(db.ConversationMessage.conversation_id == conversation.conversation_id)
                .order_by(col(db.ConversationMessage.sequence).asc())
            )

            user_participants = await session.exec(
                select(db.UserParticipant).where(db.UserParticipant.conversation_id == conversation.conversation_id)
            )

            assistant_participant = (
                await session.exec(
                    select(db.AssistantParticipant)
                    .where(db.AssistantParticipant.assistant_id == assistant.assistant_id)
                    .where(db.AssistantParticipant.conversation_id == conversation.conversation_id)
                )
            ).one()

            users = await session.exec(
                select(db.User)
                .join(
                    db.UserParticipant,
                    col(db.UserParticipant.user_id) == col(db.User.user_id),
                )
                .where(db.UserParticipant.conversation_id == conversation.conversation_id)
            )

            with (
                tempfile.NamedTemporaryFile(delete=False) as tempfile_workbench,
                tempfile.NamedTemporaryFile(delete=False) as tempfile_assistant,
                tempfile.NamedTemporaryFile(delete=False) as tempfile_conversation,
                tempfile.NamedTemporaryFile(delete=False) as tempfile_zip,
                zipfile.ZipFile(file=tempfile_zip, mode="a", compression=zipfile.ZIP_DEFLATED) as zip_file,
            ):
                for file_bytes in export_import.export_assistant_file(
                    assistant=assistant,
                    conversation=conversation,
                    messages=messages,
                    user_participants=user_participants,
                    users=users,
                    assistant_participant=assistant_participant,
                ):
                    tempfile_workbench.write(file_bytes)

                assistant_client = (
                    await self._assistant_client_builder(registration=assistant.related_assistant_service_registration)
                ).for_assistant_instance(assistant_id=assistant.assistant_id)
                async with assistant_client.get_exported_instance_data() as response:
                    async for chunk in response:
                        tempfile_assistant.write(chunk)

                async with assistant_client.get_exported_conversation_data(
                    conversation_id=conversation.conversation_id
                ) as response:
                    async for chunk in response:
                        tempfile_conversation.write(chunk)

                tempfile_workbench.flush()
                tempfile_assistant.flush()
                tempfile_conversation.flush()

                tempfile_workbench.close()
                tempfile_assistant.close()
                tempfile_conversation.close()

                zip_file.write(tempfile_workbench.name, arcname=AssistantController.EXPORT_WORKBENCH_FILENAME)
                zip_file.write(tempfile_assistant.name, arcname=AssistantController.EXPORT_ASSISTANT_DATA_FILENAME)
                zip_file.write(
                    tempfile_conversation.name, arcname=AssistantController.EXPORT_ASSISTANT_CONVERSATION_DATA_FILENAME
                )

        export_file_name = assistant.name.strip().replace(" ", "_")
        export_file_name = re.sub(r"(?u)[^-\w.]", "", export_file_name)
        export_file_name = f"assistant_{export_file_name}_{datetime.datetime.utcnow().strftime('%Y%m%d%H%M%S')}.zip"

        def _cleanup() -> None:
            os.remove(tempfile_workbench.name)
            os.remove(tempfile_assistant.name)
            os.remove(tempfile_conversation.name)
            os.remove(tempfile_zip.name)

        return ExportResult(
            file_path=tempfile_zip.name,
            content_type="application/zip",
            filename=export_file_name,
            cleanup=_cleanup,
        )

    async def import_assistant(
        self,
        from_export: BinaryIO,
        user_principal: auth.UserPrincipal,
    ) -> Assistant:
        async with self._get_session() as session:
            with (
                tempfile.TemporaryDirectory() as extraction_path,
                zipfile.ZipFile(file=from_export, mode="r") as zip_file,
            ):
                zip_file.extractall(path=extraction_path)
                zip_file.close()

                with open(
                    os.path.join(extraction_path, AssistantController.EXPORT_WORKBENCH_FILENAME), "rb"
                ) as workbench_file:
                    import_result = await export_import.import_files(
                        session=session,
                        owner_id=user_principal.user_id,
                        files=[workbench_file],
                    )

                if len(import_result.assistant_id_old_to_new) != 1:
                    raise exceptions.InvalidArgumentError(
                        detail=f"expected one assistant in export, not {len(import_result.assistant_id_old_to_new)}",
                    )

                if len(import_result.conversation_id_old_to_new) != 1:
                    raise exceptions.InvalidArgumentError(
                        detail=(
                            f"expected one conversation in export, not {len(import_result.conversation_id_old_to_new)}"
                        ),
                    )

                _, assistant_id = import_result.assistant_id_old_to_new.popitem()
                _, conversation_id = import_result.conversation_id_old_to_new.popitem()

                await db.insert_if_not_exists(
                    session,
                    db.UserParticipant(
                        conversation_id=conversation_id,
                        user_id=user_principal.user_id,
                        active_participant=True,
                    ),
                )
                importing_user_participant = (
                    await session.exec(
                        select(db.UserParticipant)
                        .where(db.UserParticipant.conversation_id == conversation_id)
                        .where(db.UserParticipant.user_id == user_principal.user_id)
                        .with_for_update()
                    )
                ).one()
                importing_user_participant.active_participant = True
                session.add(importing_user_participant)

                await session.flush()

                assistant = (
                    await session.exec(select(db.Assistant).where(db.Assistant.assistant_id == assistant_id))
                ).one()
                conversation = (
                    await session.exec(
                        select(db.Conversation).where(db.Conversation.conversation_id == conversation_id)
                    )
                ).one()

                with (
                    open(
                        os.path.join(extraction_path, AssistantController.EXPORT_ASSISTANT_DATA_FILENAME), "rb"
                    ) as assistant_file,
                    open(
                        os.path.join(extraction_path, AssistantController.EXPORT_ASSISTANT_CONVERSATION_DATA_FILENAME),
                        "rb",
                    ) as conversation_file,
                ):
                    assistant_service = (
                        await session.exec(
                            select(db.AssistantServiceRegistration).where(
                                db.AssistantServiceRegistration.assistant_service_id == assistant.assistant_service_id
                            )
                        )
                    ).one_or_none()
                    if assistant_service is None:
                        raise exceptions.InvalidArgumentError(
                            detail=f"assistant service id {assistant.assistant_service_id} is not valid"
                        )

                    try:
                        await self._put_assistant(assistant=assistant, from_export=assistant_file)
                    except AssistantError:
                        logger.error("error importing assistant", exc_info=True)
                        raise

                    try:
                        await self.connect_assistant_to_conversation(
                            conversation=conversation,
                            assistant=assistant,
                            from_export=conversation_file,
                        )
                    except AssistantError:
                        logger.error("error connecting assistant to conversation on import", exc_info=True)
                        raise

            await session.commit()
            await session.refresh(assistant)

        return await self.get_assistant(assistant_id=assistant.assistant_id)

    async def export_conversations(
        self,
        user_principal: auth.UserPrincipal,
        conversation_ids: list[uuid.UUID],
    ) -> ExportResult:
        files_to_cleanup = set()
        async with self._get_session() as session:
            with (
                tempfile.NamedTemporaryFile(delete=False) as tempfile_zip,
                zipfile.ZipFile(file=tempfile_zip, mode="a", compression=zipfile.ZIP_DEFLATED) as zip_file,
            ):
                files_to_cleanup.add(tempfile_zip.name)

                with tempfile.NamedTemporaryFile(delete=False) as tempfile_workbench:
                    files_to_cleanup.add(tempfile_workbench.name)

                    async for file_bytes in export_import.export_conversations_file(
                        conversation_ids=conversation_ids,
                        user_principal=user_principal,
                        session=session,
                    ):
                        tempfile_workbench.write(file_bytes)

                zip_file.write(tempfile_workbench.name, arcname=AssistantController.EXPORT_WORKBENCH_FILENAME)

                assistants = (
                    await session.exec(
                        select(db.Assistant)
                        .join(
                            db.AssistantParticipant,
                            col(db.AssistantParticipant.assistant_id) == col(db.Assistant.assistant_id),
                        )
                        .where(col(db.AssistantParticipant.conversation_id).in_(conversation_ids))
                    )
                ).unique()

                for assistant in assistants:
                    assistant_client = (
                        await self._assistant_client_builder(
                            registration=assistant.related_assistant_service_registration,
                        )
                    ).for_assistant_instance(assistant_id=assistant.assistant_id)

                    with tempfile.NamedTemporaryFile(delete=False) as tempfile_assistant:
                        files_to_cleanup.add(tempfile_assistant.name)

                        async with assistant_client.get_exported_instance_data() as response:
                            async for chunk in response:
                                tempfile_assistant.write(chunk)

                    archive_name = (
                        f"assistants/{assistant.assistant_id}/{AssistantController.EXPORT_ASSISTANT_DATA_FILENAME}"
                    )
                    zip_file.write(tempfile_assistant.name, arcname=archive_name)

                    assistant_participants = await session.exec(
                        select(db.AssistantParticipant)
                        .where(db.AssistantParticipant.assistant_id == assistant.assistant_id)
                        .where(col(db.AssistantParticipant.conversation_id).in_(conversation_ids))
                    )

                    for assistant_participant in assistant_participants:
                        with tempfile.NamedTemporaryFile(delete=False) as tempfile_conversation:
                            files_to_cleanup.add(tempfile_conversation.name)

                            async with assistant_client.get_exported_conversation_data(
                                conversation_id=assistant_participant.conversation_id
                            ) as response:
                                async for chunk in response:
                                    tempfile_conversation.write(chunk)

                        archive_name = (
                            f"assistants/{assistant.assistant_id}"
                            f"/conversations/{assistant_participant.conversation_id}"
                            f"/{AssistantController.EXPORT_ASSISTANT_CONVERSATION_DATA_FILENAME}"
                        )
                        zip_file.write(tempfile_conversation.name, arcname=archive_name)

        export_file_name = (
            f"semantic_workbench_conversation_export_{datetime.datetime.utcnow().strftime('%Y%m%d%H%M%S')}.zip"
        )

        def _cleanup():
            for file_name in files_to_cleanup:
                os.remove(file_name)

        return ExportResult(
            file_path=tempfile_zip.name,
            content_type="application/zip",
            filename=export_file_name,
            cleanup=_cleanup,
        )

    async def import_conversations(
        self,
        from_export: BinaryIO,
        user_principal: auth.UserPrincipal,
    ) -> ConversationImportResult:
        async with self._get_session() as session:
            with (
                tempfile.TemporaryDirectory() as extraction_path,
                zipfile.ZipFile(file=from_export, mode="r") as zip_file,
            ):
                zip_file.extractall(path=extraction_path)
                zip_file.close()

                with (
                    open(
                        os.path.join(extraction_path, AssistantController.EXPORT_WORKBENCH_FILENAME), "rb"
                    ) as workbench_file,
                ):
                    import_result = await export_import.import_files(
                        session=session,
                        owner_id=user_principal.user_id,
                        files=[workbench_file],
                    )

                # ensure that the user is a participant in all imported conversations, in case they are
                # importing another user's export
                for _, conversation_id in import_result.conversation_id_old_to_new.items():
                    await db.insert_if_not_exists(
                        session,
                        db.UserParticipant(
                            conversation_id=conversation_id,
                            user_id=user_principal.user_id,
                            active_participant=True,
                        ),
                    )

                    importing_user_participant = (
                        await session.exec(
                            select(db.UserParticipant)
                            .where(db.UserParticipant.conversation_id == conversation_id)
                            .where(db.UserParticipant.user_id == user_principal.user_id)
                            .with_for_update()
                        )
                    ).one()
                    importing_user_participant.active_participant = True
                    session.add(importing_user_participant)

                await session.flush()

                for old_assistant_id, new_assistant_id in import_result.assistant_id_old_to_new.items():
                    assistant = (
                        await session.exec(select(db.Assistant).where(db.Assistant.assistant_id == new_assistant_id))
                    ).one()

                    assistant_service = (
                        await session.exec(
                            select(db.AssistantServiceRegistration).where(
                                db.AssistantServiceRegistration.assistant_service_id == assistant.assistant_service_id
                            )
                        )
                    ).one_or_none()
                    if assistant_service is None:
                        raise exceptions.InvalidArgumentError(
                            detail=f"assistant service id {assistant.assistant_service_id} is not valid"
                        )

                    archive_name = f"assistants/{old_assistant_id}/{AssistantController.EXPORT_ASSISTANT_DATA_FILENAME}"
                    with open(os.path.join(extraction_path, archive_name), "rb") as assistant_file:
                        try:
                            await self._put_assistant(
                                assistant=assistant,
                                from_export=assistant_file,
                            )
                        except AssistantError:
                            logger.error("error creating assistant on import", exc_info=True)
                            raise

                        for old_conversation_id in import_result.assistant_conversation_old_ids[old_assistant_id]:
                            archive_name = (
                                f"assistants/{old_assistant_id}"
                                f"/conversations/{old_conversation_id}"
                                f"/{AssistantController.EXPORT_ASSISTANT_CONVERSATION_DATA_FILENAME}"
                            )

                            new_conversation_id = import_result.conversation_id_old_to_new[old_conversation_id]
                            new_conversation = (
                                await session.exec(
                                    select(db.Conversation).where(
                                        db.Conversation.conversation_id == new_conversation_id
                                    )
                                )
                            ).one()

                            with open(os.path.join(extraction_path, archive_name), "rb") as conversation_file:
                                try:
                                    await self.connect_assistant_to_conversation(
                                        conversation=new_conversation,
                                        assistant=assistant,
                                        from_export=conversation_file,
                                    )
                                except AssistantError:
                                    logger.error("error connecting assistant to conversation on import", exc_info=True)
                                    raise

            await session.commit()

        return ConversationImportResult(
            assistant_ids=list(import_result.assistant_id_old_to_new.values()),
            conversation_ids=list(import_result.conversation_id_old_to_new.values()),
        )
