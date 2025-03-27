import uuid
from typing import (
    Any,
    AsyncContextManager,
    Awaitable,
    Callable,
    Generator,
    Iterable,
    NamedTuple,
)

from fastapi import UploadFile
from semantic_workbench_api_model.workbench_model import (
    ConversationEvent,
    ConversationEventType,
    FileList,
    FileVersions,
)
from sqlmodel import col, select
from sqlmodel.ext.asyncio.session import AsyncSession

from .. import auth, db, files, query
from ..event import ConversationEventQueueItem
from . import convert, exceptions

DownloadFileResult = NamedTuple(
    "DownloadFileResult", [("filename", str), ("content_type", str), ("stream", Iterable[bytes])]
)


class FileController:
    def __init__(
        self,
        get_session: Callable[[], AsyncContextManager[AsyncSession]],
        notify_event: Callable[[ConversationEventQueueItem], Awaitable],
        file_storage: files.Storage,
    ) -> None:
        self._get_session = get_session
        self._notify_event = notify_event
        self._file_storage = file_storage

    async def upload_files(
        self,
        conversation_id: uuid.UUID,
        upload_files: list[UploadFile],
        principal: auth.ActorPrincipal,
        file_metadata: dict[str, Any],
    ) -> FileList:
        if len(upload_files) > 10:
            raise exceptions.InvalidArgumentError(detail="file uploads limited to 10 at a time")

        unique_filenames = {f.filename for f in upload_files}
        if len([f for f in unique_filenames if not f]) > 0:
            raise exceptions.InvalidArgumentError(detail="filename is required for all file uploads")

        if len(unique_filenames) != len(upload_files):
            raise exceptions.InvalidArgumentError(detail="filenames are required to be unique")

        async with self._get_session() as session:
            conversation = (
                await session.exec(
                    query.select_conversations_for(principal).where(db.Conversation.conversation_id == conversation_id)
                )
            ).one_or_none()
            if conversation is None:
                raise exceptions.NotFoundError()

            existing_files = (
                await session.exec(
                    select(db.File)
                    .where(db.File.conversation_id == conversation_id)
                    .where(col(db.File.filename).in_(unique_filenames))
                    .with_for_update()
                )
            ).all()

            file_record_and_uploads = [
                (
                    next(
                        (f for f in existing_files if f.filename == upload_file.filename),
                        db.File(
                            conversation_id=conversation_id,
                            filename=upload_file.filename,
                            current_version=0,
                        ),
                    ),
                    upload_file,
                )
                for upload_file in upload_files
                if upload_file.filename
            ]

            match principal:
                case auth.UserPrincipal():
                    role = "user"
                    participant_id = principal.user_id
                case auth.AssistantServicePrincipal():
                    role = "assistant"
                    participant_id = str(principal.assistant_id)

            file_record_and_versions: list[tuple[db.File, db.FileVersion]] = []

            for file_record, upload_file in file_record_and_uploads:
                file_record.current_version += 1
                new_version = db.FileVersion(
                    file_id=file_record.file_id,
                    participant_role=role,
                    participant_id=participant_id,
                    version=file_record.current_version,
                    content_type=upload_file.content_type or "",
                    file_size=upload_file.size or 0,
                    meta_data=file_metadata.get(file_record.filename, {}),
                    storage_filename=f"{file_record.file_id.hex}_{file_record.current_version}",
                )
                file_record_and_versions.append((file_record, new_version))

                self._file_storage.write_file(
                    namespace=str(conversation_id),
                    filename=new_version.storage_filename,
                    content=upload_file.file,
                )
                session.add(file_record)
                session.add(new_version)

                await self._notify_event(
                    ConversationEventQueueItem(
                        event=ConversationEvent(
                            conversation_id=conversation_id,
                            event=(
                                ConversationEventType.file_created
                                if new_version.version == 1
                                else ConversationEventType.file_updated
                            ),
                            data={
                                "file": convert.file_from_db((file_record, new_version)).model_dump(),
                            },
                        ),
                    )
                )

            await session.commit()

            return convert.file_list_from_db(file_record_and_versions)

    async def list_files(
        self,
        conversation_id: uuid.UUID,
        principal: auth.ActorPrincipal,
        prefix: str | None = None,
    ) -> FileList:
        async with self._get_session() as session:
            conversation = (
                await session.exec(
                    query.select_conversations_for(principal, include_all_owned=True, include_observer=True).where(
                        db.Conversation.conversation_id == conversation_id
                    )
                )
            ).one_or_none()
            if conversation is None:
                raise exceptions.NotFoundError()

            select_query = (
                select(db.File, db.FileVersion)
                .join(db.FileVersion)
                .where(db.File.current_version == db.FileVersion.version)
                .where(db.File.conversation_id == conversation_id)
            )
            if prefix is not None:
                select_query = select_query.where(db.File.filename.startswith(prefix))
            select_query = select_query.order_by(col(db.File.filename).asc())
            files = await session.exec(select_query)

            return convert.file_list_from_db(files)

    async def file_versions(
        self,
        conversation_id: uuid.UUID,
        filename: str,
        principal: auth.ActorPrincipal,
        version: int | None = None,
    ) -> FileVersions:
        async with self._get_session() as session:
            conversation = (
                await session.exec(
                    query.select_conversations_for(principal, include_all_owned=True, include_observer=True).where(
                        db.Conversation.conversation_id == conversation_id
                    )
                )
            ).one_or_none()
            if conversation is None:
                raise exceptions.NotFoundError()

            select_query = (
                select(db.File, db.FileVersion)
                .join(db.FileVersion)
                .where(db.File.conversation_id == conversation_id)
                .where(db.File.filename == filename)
            )
            if version is not None:
                select_query = select_query.where(db.FileVersion.version == version)
            select_query = select_query.order_by(col(db.FileVersion.version).asc())

            file_records = (await session.exec(select_query)).all()
            if not file_records:
                raise exceptions.NotFoundError()

            return convert.file_versions_from_db(
                file=file_records[0][0],
                versions=(version for _, version in file_records),
            )

    async def update_file_metadata(
        self,
        conversation_id: uuid.UUID,
        filename: str,
        principal: auth.ActorPrincipal,
        metadata: dict[str, Any],
    ) -> FileVersions:
        async with self._get_session() as session:
            conversation = (
                await session.exec(
                    query.select_conversations_for(principal, include_all_owned=True).where(
                        db.Conversation.conversation_id == conversation_id
                    )
                )
            ).one_or_none()
            if conversation is None:
                raise exceptions.NotFoundError()

            record_pair = (
                await session.exec(
                    (
                        select(db.File, db.FileVersion)
                        .join(db.FileVersion)
                        .where(db.File.conversation_id == conversation_id)
                        .where(db.File.filename == filename)
                        .order_by(col(db.FileVersion.version).desc())
                        .limit(1)
                    )
                )
            ).one_or_none()
            if record_pair is None:
                raise exceptions.NotFoundError()

            file_record, version_record = record_pair
            version_record.meta_data = {**version_record.meta_data, **metadata}

            session.add(version_record)
            await session.commit()

        await self._notify_event(
            ConversationEventQueueItem(
                event=ConversationEvent(
                    conversation_id=conversation_id,
                    event=ConversationEventType.file_updated,
                    data={
                        "file": convert.file_from_db((file_record, version_record)).model_dump(),
                    },
                ),
            )
        )

        return await self.file_versions(
            conversation_id=conversation_id,
            filename=filename,
            principal=principal,
            version=version_record.version,
        )

    async def download_file(
        self,
        conversation_id: uuid.UUID,
        filename: str,
        principal: auth.ActorPrincipal,
        version: int | None = None,
    ) -> DownloadFileResult:
        async with self._get_session() as session:
            conversation = (
                await session.exec(
                    query.select_conversations_for(principal, include_all_owned=True, include_observer=True).where(
                        db.Conversation.conversation_id == conversation_id
                    )
                )
            ).one_or_none()
            if conversation is None:
                raise exceptions.NotFoundError()

            select_query = (
                select(db.File, db.FileVersion)
                .join(db.FileVersion)
                .where(db.File.conversation_id == conversation_id)
                .where(db.File.filename == filename)
            )
            if version is not None:
                select_query = select_query.where(db.FileVersion.version == version)
            else:
                select_query = select_query.where(db.File.current_version == db.FileVersion.version)

            file_records = (await session.exec(select_query)).one_or_none()
            if file_records is None:
                raise exceptions.NotFoundError()

            file_record, version_record = file_records

        def generator_wrapper() -> Generator[bytes, Any, None]:
            with self._file_storage.read_file(
                namespace=str(conversation_id),
                filename=version_record.storage_filename,
            ) as file:
                for chunk in iter(lambda: file.read(100 * 1_024), b""):
                    yield chunk

        filename = file_record.filename.split("/")[-1]

        return DownloadFileResult(
            filename=filename,
            content_type=version_record.content_type,
            stream=generator_wrapper(),
        )

    async def delete_file(
        self,
        conversation_id: uuid.UUID,
        filename: str,
        principal: auth.ActorPrincipal,
    ) -> None:
        async with self._get_session() as session:
            conversation = (
                await session.exec(
                    query.select_conversations_for(principal).where(db.Conversation.conversation_id == conversation_id)
                )
            ).one_or_none()
            if conversation is None:
                raise exceptions.NotFoundError()

            file_record = (
                await session.exec(
                    select(db.File)
                    .where(db.File.conversation_id == conversation_id)
                    .where(db.File.filename == filename)
                )
            ).one_or_none()
            if file_record is None:
                raise exceptions.NotFoundError()

            current_version = (
                await session.exec(
                    select(db.FileVersion)
                    .where(db.FileVersion.file_id == file_record.file_id)
                    .where(db.FileVersion.version == file_record.current_version)
                )
            ).one()

            version_records = (
                await session.exec(select(db.FileVersion).where(db.FileVersion.file_id == file_record.file_id))
            ).all()

            for version_record in version_records:
                self._file_storage.delete_file(
                    namespace=str(conversation_id),
                    filename=version_record.storage_filename,
                )
                await session.delete(version_record)
            await session.commit()

            await session.delete(file_record)
            await session.commit()

        await self._notify_event(
            ConversationEventQueueItem(
                event=ConversationEvent(
                    conversation_id=conversation_id,
                    event=ConversationEventType.file_deleted,
                    data={
                        "file": convert.file_from_db((file_record, current_version)).model_dump(),
                    },
                ),
            )
        )
