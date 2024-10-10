import asyncio
import datetime
import logging
import pathlib
import re
import shutil
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
from sqlalchemy.orm import joinedload
from sqlmodel import col, select
from sqlmodel.ext.asyncio.session import AsyncSession

from .. import auth, db, files, query
from ..event import ConversationEventQueueItem
from . import convert, exceptions, export_import
from . import participant as participant_
from . import user as user_
from .assistant_service_client_pool import AssistantServiceClientPool

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
        client_pool: AssistantServiceClientPool,
        file_storage: files.Storage,
    ) -> None:
        self._get_session = get_session
        self._notify_event = notify_event
        self._client_pool = client_pool
        self._file_storage = file_storage

    async def _ensure_assistant(
        self,
        session: AsyncSession,
        assistant_id: uuid.UUID,
        principal: auth.AssistantPrincipal | auth.UserPrincipal,
        include_assistants_from_conversations: bool = False,
    ) -> db.Assistant:
        match principal:
            case auth.UserPrincipal():
                assistant = (
                    await session.exec(
                        query.select_assistants_for(
                            user_principal=principal,
                            include_assistants_from_conversations=include_assistants_from_conversations,
                        ).where(db.Assistant.assistant_id == assistant_id)
                    )
                ).one_or_none()

            case auth.AssistantPrincipal():
                assistant = (
                    await session.exec(
                        query.select(db.Assistant)
                        .where(db.Assistant.assistant_id == assistant_id)
                        .where(db.Assistant.assistant_id == principal.assistant_id)
                        .where(db.Assistant.assistant_service_id == principal.assistant_service_id)
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
            await self._client_pool.service_client(
                registration=assistant.related_assistant_service_registration,
            )
        ).put_assistant_instance(
            assistant_id=assistant.assistant_id,
            request=AssistantPutRequestModel(assistant_name=assistant.name),
            from_export=from_export,
        )

    async def forward_event_to_assistant(self, assistant_id: uuid.UUID, event: ConversationEvent) -> None:
        async with self._get_session() as session:
            assistant = (
                await session.exec(
                    select(db.Assistant)
                    .where(db.Assistant.assistant_id == assistant_id)
                    .options(joinedload(db.Assistant.related_assistant_service_registration, innerjoin=True))
                )
            ).one()

        try:
            await (await self._client_pool.assistant_instance_client(assistant)).post_conversation_event(event=event)
        except AssistantError as e:
            if e.status_code != httpx.codes.NOT_FOUND:
                logger.exception(
                    "error forwarding event to assistant; assistant_id: %s, conversation_id: %s, event: %s",
                    assistant.assistant_id,
                    event.conversation_id,
                    event,
                )

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
                col(db.AssistantParticipant.active_participant).is_(True),
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
                        event_type=ConversationEventType.participant_updated,
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
        await (await self._client_pool.assistant_instance_client(assistant)).delete_conversation(
            conversation_id=conversation_id
        )

    async def connect_assistant_to_conversation(
        self, conversation: db.Conversation, assistant: db.Assistant, from_export: IO[bytes] | None
    ) -> None:
        await (await self._client_pool.assistant_instance_client(assistant)).put_conversation(
            ConversationPutRequestModel(id=str(conversation.conversation_id), title=conversation.title),
            from_export=from_export,
        )

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
                imported_from_assistant_id=None,
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

        return await self.get_assistant(user_principal=user_principal, assistant_id=assistant.assistant_id)

    async def update_assistant(
        self,
        user_principal: auth.UserPrincipal,
        assistant_id: uuid.UUID,
        update_assistant: UpdateAssistant,
    ) -> Assistant:
        async with self._get_session() as session:
            assistant = (
                await session.exec(
                    query.select_assistants_for(
                        user_principal=user_principal,
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

        return await self.get_assistant(user_principal=user_principal, assistant_id=assistant.assistant_id)

    async def delete_assistant(
        self,
        user_principal: auth.UserPrincipal,
        assistant_id: uuid.UUID,
    ) -> None:
        async with self._get_session() as session:
            assistant = (
                await session.exec(
                    query.select_assistants_for(
                        user_principal=user_principal,
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
                    .where(
                        db.AssistantParticipant.assistant_id == assistant_id,
                        col(db.AssistantParticipant.active_participant).is_(True),
                    )
                )
            ).all()

            for conversation in conversations:
                await self._remove_assistant_from_conversation(
                    session=session,
                    assistant=assistant,
                    conversation_id=conversation.conversation_id,
                )

            try:
                await (
                    await self._client_pool.service_client(assistant.related_assistant_service_registration)
                ).delete_assistant_instance(assistant_id=assistant.assistant_id)

            except AssistantError:
                logger.exception("error disconnecting assistant")

            await session.delete(assistant)
            await session.commit()

    async def get_assistants(
        self,
        user_principal: auth.UserPrincipal,
        conversation_id: uuid.UUID | None = None,
    ) -> AssistantList:
        async with self._get_session() as session:
            if conversation_id is None:
                assistants = await session.exec(
                    query.select_assistants_for(user_principal=user_principal).order_by(
                        col(db.Assistant.created_datetime).desc(),
                        col(db.Assistant.name).asc(),
                    )
                )

                return convert.assistant_list_from_db(models=assistants)

            conversation = (
                await session.exec(
                    query.select_conversations_for(
                        principal=user_principal, include_all_owned=True, include_observer=True
                    ).where(db.Conversation.conversation_id == conversation_id)
                )
            ).one_or_none()
            if conversation is None:
                raise exceptions.NotFoundError()

            assistants = await session.exec(
                select(db.Assistant)
                .join(
                    db.AssistantParticipant, col(db.Assistant.assistant_id) == col(db.AssistantParticipant.assistant_id)
                )
                .where(col(db.AssistantParticipant.active_participant).is_(True))
                .where(db.AssistantParticipant.conversation_id == conversation_id)
            )

            return convert.assistant_list_from_db(models=assistants)

    async def get_assistant(
        self,
        user_principal: auth.UserPrincipal,
        assistant_id: uuid.UUID,
    ) -> Assistant:
        async with self._get_session() as session:
            assistant = await self._ensure_assistant(
                principal=user_principal,
                assistant_id=assistant_id,
                session=session,
                include_assistants_from_conversations=True,
            )
            return convert.assistant_from_db(model=assistant)

    async def get_assistant_config(
        self,
        user_principal: auth.UserPrincipal,
        assistant_id: uuid.UUID,
    ) -> ConfigResponseModel:
        async with self._get_session() as session:
            assistant = await self._ensure_assistant(
                principal=user_principal, assistant_id=assistant_id, session=session
            )

        return await (await self._client_pool.assistant_instance_client(assistant)).get_config()

    async def update_assistant_config(
        self,
        user_principal: auth.UserPrincipal,
        assistant_id: uuid.UUID,
        updated_config: ConfigPutRequestModel,
    ) -> ConfigResponseModel:
        async with self._get_session() as session:
            assistant = await self._ensure_assistant(
                principal=user_principal, assistant_id=assistant_id, session=session
            )

        return await (await self._client_pool.assistant_instance_client(assistant)).put_config(updated_config)

    async def get_assistant_conversation_state_descriptions(
        self,
        user_principal: auth.UserPrincipal,
        assistant_id: uuid.UUID,
        conversation_id: uuid.UUID,
    ) -> StateDescriptionListResponseModel:
        async with self._get_session() as session:
            assistant = await self._ensure_assistant(
                principal=user_principal,
                assistant_id=assistant_id,
                session=session,
                include_assistants_from_conversations=True,
            )
            await self._ensure_assistant_conversation(
                assistant=assistant, conversation_id=conversation_id, session=session
            )

        return await (await self._client_pool.assistant_instance_client(assistant)).get_state_descriptions(
            conversation_id=conversation_id
        )

    async def get_assistant_conversation_state(
        self,
        user_principal: auth.UserPrincipal,
        assistant_id: uuid.UUID,
        conversation_id: uuid.UUID,
        state_id: str,
    ) -> StateResponseModel:
        async with self._get_session() as session:
            assistant = await self._ensure_assistant(
                principal=user_principal,
                assistant_id=assistant_id,
                session=session,
                include_assistants_from_conversations=True,
            )
            await self._ensure_assistant_conversation(
                assistant=assistant, conversation_id=conversation_id, session=session
            )

        return await (await self._client_pool.assistant_instance_client(assistant)).get_state(
            conversation_id=conversation_id, state_id=state_id
        )

    async def update_assistant_conversation_state(
        self,
        user_principal: auth.UserPrincipal,
        assistant_id: uuid.UUID,
        conversation_id: uuid.UUID,
        state_id: str,
        updated_state: StatePutRequestModel,
    ) -> StateResponseModel:
        async with self._get_session() as session:
            assistant = await self._ensure_assistant(
                principal=user_principal,
                assistant_id=assistant_id,
                session=session,
                include_assistants_from_conversations=True,
            )
            await self._ensure_assistant_conversation(
                assistant=assistant, conversation_id=conversation_id, session=session
            )

        return await (await self._client_pool.assistant_instance_client(assistant)).put_state(
            conversation_id=conversation_id, state_id=state_id, updated_state=updated_state
        )

    async def post_assistant_state_event(
        self,
        assistant_id: uuid.UUID,
        state_event: AssistantStateEvent,
        assistant_principal: auth.AssistantPrincipal,
        conversation_ids: list[uuid.UUID] = [],
    ) -> None:
        async with self._get_session() as session:
            await self._ensure_assistant(principal=assistant_principal, assistant_id=assistant_id, session=session)

            if not conversation_ids:
                for participant in await session.exec(
                    select(db.AssistantParticipant).where(
                        db.AssistantParticipant.assistant_id == assistant_id,
                        col(db.AssistantParticipant.active_participant).is_(True),
                    )
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
        user_principal: auth.UserPrincipal,
        assistant_id: uuid.UUID,
    ) -> ExportResult:
        async with self._get_session() as session:
            assistant = await self._ensure_assistant(
                session=session, assistant_id=assistant_id, principal=user_principal
            )

            conversations = await session.exec(
                query.select_conversations_for(principal=user_principal, include_all_owned=True)
                .join(db.AssistantParticipant)
                .where(
                    db.AssistantParticipant.assistant_id == assistant_id,
                    col(db.AssistantParticipant.active_participant).is_(True),
                )
            )
            conversation_ids = {conversation.conversation_id for conversation in conversations}

            export_file_name = assistant.name.strip().replace(" ", "_")
            export_file_name = re.sub(r"(?u)[^-\w.]", "", export_file_name)
            export_file_name = (
                f"assistant_{export_file_name}_{datetime.datetime.now(datetime.UTC).strftime('%Y%m%d%H%M%S')}"
            )

            return await self._export(
                session=session,
                export_filename_prefix=export_file_name,
                conversation_ids=conversation_ids,
                assistant_ids=set((assistant_id,)),
            )

    async def _export(
        self,
        conversation_ids: set[uuid.UUID],
        assistant_ids: set[uuid.UUID],
        session: AsyncSession,
        export_filename_prefix: str,
    ) -> ExportResult:
        temp_dir_path = pathlib.Path(tempfile.mkdtemp())

        # write all files to a temporary directory
        export_dir_path = temp_dir_path / "export"
        export_dir_path.mkdir()

        # export records from database
        with (export_dir_path / AssistantController.EXPORT_WORKBENCH_FILENAME).open("+wb") as workbench_file:
            async for file_bytes in export_import.export_file(
                conversation_ids=conversation_ids,
                assistant_ids=assistant_ids,
                session=session,
            ):
                workbench_file.write(file_bytes)

        # export files from storage
        for conversation_id in conversation_ids:
            source_dir = self._file_storage.path_for(namespace=str(conversation_id), filename="")
            if not source_dir.is_dir():
                continue

            conversation_dir = export_dir_path / "files" / str(conversation_id)
            conversation_dir.mkdir(parents=True)

            await asyncio.to_thread(shutil.copytree, src=source_dir, dst=conversation_dir, dirs_exist_ok=True)

        # enumerate assistants
        assistants = await session.exec(select(db.Assistant).where(col(db.Assistant.assistant_id).in_(assistant_ids)))

        for assistant in assistants:
            assistant_client = await self._client_pool.assistant_instance_client(assistant)

            # export assistant data
            assistant_dir = export_dir_path / "assistants" / str(assistant.assistant_id)
            assistant_dir.mkdir(parents=True)

            with (assistant_dir / AssistantController.EXPORT_ASSISTANT_DATA_FILENAME).open("wb") as assistant_file:
                async with assistant_client.get_exported_instance_data() as response:
                    async for chunk in response:
                        assistant_file.write(chunk)

            # enumerate assistant conversations
            assistant_participants = await session.exec(
                select(db.AssistantParticipant)
                .where(db.AssistantParticipant.assistant_id == assistant.assistant_id)
                .where(col(db.AssistantParticipant.conversation_id).in_(conversation_ids))
            )

            for assistant_participant in assistant_participants:
                conversation_dir = assistant_dir / "conversations" / str(assistant_participant.conversation_id)
                conversation_dir.mkdir(parents=True)

                # export assistant conversation data
                with (conversation_dir / AssistantController.EXPORT_ASSISTANT_CONVERSATION_DATA_FILENAME).open(
                    "wb"
                ) as conversation_file:
                    async with assistant_client.get_exported_conversation_data(
                        conversation_id=assistant_participant.conversation_id
                    ) as response:
                        async for chunk in response:
                            conversation_file.write(chunk)

        # zip the export directory
        zip_file_path = await asyncio.to_thread(
            shutil.make_archive,
            base_name=str(temp_dir_path / "zip"),
            format="zip",
            root_dir=export_dir_path,
            base_dir="",
            logger=logger,
            verbose=True,
        )

        def _cleanup() -> None:
            shutil.rmtree(temp_dir_path, ignore_errors=True)

        return ExportResult(
            file_path=zip_file_path,
            content_type="application/zip",
            filename=export_filename_prefix + ".zip",
            cleanup=_cleanup,
        )

    async def export_conversations(
        self,
        user_principal: auth.UserPrincipal,
        conversation_ids: set[uuid.UUID],
    ) -> ExportResult:
        async with self._get_session() as session:
            conversations = await session.exec(
                query.select_conversations_for(
                    principal=user_principal, include_all_owned=True, include_observer=True
                ).where(col(db.Conversation.conversation_id).in_(conversation_ids))
            )
            conversation_ids = {conversation.conversation_id for conversation in conversations}

            assistant_ids = set(
                (
                    await session.exec(
                        select(db.Assistant.assistant_id)
                        .join(
                            db.AssistantParticipant,
                            col(db.AssistantParticipant.assistant_id) == col(db.Assistant.assistant_id),
                        )
                        .where(
                            col(db.AssistantParticipant.active_participant).is_(True),
                            col(db.AssistantParticipant.conversation_id).in_(conversation_ids),
                        )
                    )
                ).unique()
            )

            return await self._export(
                session=session,
                export_filename_prefix=(
                    f"semantic_workbench_conversation_export_{datetime.datetime.now(datetime.UTC).strftime('%Y%m%d%H%M%S')}"
                ),
                conversation_ids=conversation_ids,
                assistant_ids=assistant_ids,
            )

    async def import_conversations(
        self,
        from_export: BinaryIO,
        user_principal: auth.UserPrincipal,
    ) -> ConversationImportResult:
        async with self._get_session() as session:
            with tempfile.TemporaryDirectory() as extraction_dir:
                extraction_path = pathlib.Path(extraction_dir)

                # extract the zip file to a temporary directory
                with zipfile.ZipFile(file=from_export, mode="r") as zip_file:
                    await asyncio.to_thread(zip_file.extractall, path=extraction_path)

                # import records into database
                with (extraction_path / AssistantController.EXPORT_WORKBENCH_FILENAME).open("rb") as workbench_file:
                    import_result = await export_import.import_files(
                        session=session,
                        owner_id=user_principal.user_id,
                        files=[workbench_file],
                    )

                await session.commit()

                # import files into storage
                for old_conversation_id, new_conversation_id in import_result.conversation_id_old_to_new.items():
                    files_path = extraction_path / "files" / str(old_conversation_id)
                    if not files_path.is_dir():
                        continue

                    storage_path = self._file_storage.path_for(namespace=str(new_conversation_id), filename="")
                    await asyncio.to_thread(shutil.copytree, src=files_path, dst=storage_path)

                try:
                    # enumerate assistants
                    for old_assistant_id, new_assistant_id in import_result.assistant_id_old_to_new.items():
                        assistant = (
                            await session.exec(
                                select(db.Assistant).where(db.Assistant.assistant_id == new_assistant_id)
                            )
                        ).one()

                        assistant_service = (
                            await session.exec(
                                select(db.AssistantServiceRegistration).where(
                                    db.AssistantServiceRegistration.assistant_service_id
                                    == assistant.assistant_service_id
                                )
                            )
                        ).one_or_none()
                        if assistant_service is None:
                            raise exceptions.InvalidArgumentError(
                                detail=f"assistant service id {assistant.assistant_service_id} is not valid"
                            )

                        assistant_dir = extraction_path / "assistants" / str(old_assistant_id)

                        # create the assistant from the assistant data file
                        with (assistant_dir / AssistantController.EXPORT_ASSISTANT_DATA_FILENAME).open(
                            "rb"
                        ) as assistant_file:
                            try:
                                await self._put_assistant(
                                    assistant=assistant,
                                    from_export=assistant_file,
                                )
                            except AssistantError:
                                logger.error("error creating assistant on import", exc_info=True)
                                raise

                            # enumerate assistant conversations
                            for old_conversation_id in import_result.assistant_conversation_old_ids[old_assistant_id]:
                                new_conversation_id = import_result.conversation_id_old_to_new[old_conversation_id]
                                new_conversation = (
                                    await session.exec(
                                        select(db.Conversation).where(
                                            db.Conversation.conversation_id == new_conversation_id
                                        )
                                    )
                                ).one()

                                conversation_dir = assistant_dir / "conversations" / str(old_conversation_id)

                                # create the conversation from the conversation data file
                                with (
                                    conversation_dir / AssistantController.EXPORT_ASSISTANT_CONVERSATION_DATA_FILENAME
                                ).open("rb") as conversation_file:
                                    try:
                                        await self.connect_assistant_to_conversation(
                                            conversation=new_conversation,
                                            assistant=assistant,
                                            from_export=conversation_file,
                                        )
                                    except AssistantError:
                                        logger.error(
                                            "error connecting assistant to conversation on import", exc_info=True
                                        )
                                        raise

                except Exception:
                    async with self._get_session() as session_delete:
                        for new_assistant_id in import_result.assistant_id_old_to_new.values():
                            assistant = (
                                await session_delete.exec(
                                    select(db.Assistant).where(db.Assistant.assistant_id == new_assistant_id)
                                )
                            ).one_or_none()
                            if assistant is not None:
                                await session_delete.delete(assistant)
                        for new_conversation_id in import_result.conversation_id_old_to_new.values():
                            conversation = (
                                await session_delete.exec(
                                    select(db.Conversation).where(
                                        db.Conversation.conversation_id == new_conversation_id
                                    )
                                )
                            ).one_or_none()
                            if conversation is not None:
                                await session_delete.delete(conversation)
                        await session_delete.commit()

                    raise

            await session.commit()

        return ConversationImportResult(
            assistant_ids=list(import_result.assistant_id_old_to_new.values()),
            conversation_ids=list(import_result.conversation_id_old_to_new.values()),
        )
