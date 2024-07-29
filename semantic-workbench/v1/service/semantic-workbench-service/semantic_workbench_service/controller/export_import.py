import collections
import datetime
import re
import tempfile
import uuid
from operator import or_
from typing import IO, Any, AsyncGenerator, Generator, Iterable, Iterator

from attr import dataclass
from pydantic import BaseModel
from sqlalchemy import ScalarResult, func
from sqlmodel import SQLModel, col, select
from sqlmodel.ext.asyncio.session import AsyncSession

from .. import auth, db, query


class _Record(BaseModel):
    type: str
    data: dict[str, Any]


def _model_record(model: SQLModel) -> _Record:
    data = model.model_dump(mode="json")
    return _Record(type=model.__class__.__name__, data=data)


def _lines_from(records: Iterator[_Record]) -> Generator[bytes, None, None]:
    for record in records:
        yield (record.model_dump_json() + "\n").encode("utf-8")


async def export_conversations_file(
    conversation_ids: Iterable[uuid.UUID],
    user_principal: auth.UserPrincipal,
    session: AsyncSession,
) -> AsyncGenerator[bytes, None]:
    users = (
        await session.exec(
            select(db.User)
            .join(db.UserParticipant, col(db.UserParticipant.user_id) == col(db.User.user_id))
            .where(col(db.UserParticipant.conversation_id).in_(conversation_ids))
        )
    ).unique()

    assistants = (
        await session.exec(
            select(db.Assistant)
            .join(db.AssistantParticipant, col(db.AssistantParticipant.assistant_id) == col(db.Assistant.assistant_id))
            .where(col(db.AssistantParticipant.conversation_id).in_(conversation_ids))
        )
    ).unique()

    conversations = await session.exec(
        query.select_conversations_for(principal=user_principal, include_inactive=True)
        .where(col(db.Conversation.conversation_id).in_(conversation_ids))
        .order_by(col(db.Conversation.conversation_id).asc())
    )

    messages = await session.exec(
        select(db.ConversationMessage)
        .where(col(db.ConversationMessage.conversation_id).in_(conversation_ids))
        .order_by(col(db.ConversationMessage.conversation_id).asc())
        .order_by(col(db.ConversationMessage.sequence).asc())
    )

    user_participants = await session.exec(
        select(db.UserParticipant)
        .where(col(db.UserParticipant.conversation_id).in_(conversation_ids))
        .order_by(col(db.UserParticipant.conversation_id).asc())
        .order_by(col(db.UserParticipant.joined_datetime).asc())
    )

    assistant_participants = await session.exec(
        select(db.AssistantParticipant)
        .where(col(db.AssistantParticipant.conversation_id).in_(conversation_ids))
        .order_by(col(db.AssistantParticipant.conversation_id).asc())
        .order_by(col(db.AssistantParticipant.joined_datetime).asc())
    )

    def _records(*sources: ScalarResult) -> Generator[_Record, None, None]:
        for source in sources:
            for record in source:
                yield _model_record(record)

    with tempfile.TemporaryFile() as f:
        f.writelines(
            _lines_from(_records(users, assistants, conversations, messages, user_participants, assistant_participants))
        )
        f.seek(0)
        for line in iter(lambda: f.readline(), b""):
            yield line


def export_assistant_file(
    assistant: db.Assistant,
    conversation: db.Conversation,
    messages: Iterable[db.ConversationMessage],
    users: Iterable[db.User],
    user_participants: Iterable[db.UserParticipant],
    assistant_participant: db.AssistantParticipant,
) -> Generator[bytes, None, None]:
    def _records() -> Generator[_Record, None, None]:
        for user in users:
            yield _model_record(user)

        yield _model_record(assistant)

        yield _model_record(conversation)

        for message in messages:
            yield _model_record(message)

        for participant in user_participants:
            yield _model_record(participant)

        yield _model_record(assistant_participant)

    with tempfile.TemporaryFile() as f:
        f.writelines(_lines_from(_records()))
        f.seek(0)
        yield from f


@dataclass
class ImportResult:
    assistant_id_old_to_new: dict[uuid.UUID, uuid.UUID]
    conversation_id_old_to_new: dict[uuid.UUID, uuid.UUID]
    assistant_conversation_old_ids: dict[uuid.UUID, set[uuid.UUID]]


async def import_files(session: AsyncSession, owner_id: str, files: Iterable[IO[bytes]]) -> ImportResult:
    result = ImportResult(
        assistant_id_old_to_new={},
        conversation_id_old_to_new={},
        assistant_conversation_old_ids=collections.defaultdict(set),
    )

    async def _process_record(record: _Record) -> None:
        match record.type:
            case db.Assistant.__name__:
                assistant = db.Assistant.model_validate(record.data)
                assistant.created_datetime = datetime.datetime.utcnow()
                result.assistant_id_old_to_new[assistant.assistant_id] = uuid.uuid4()
                assistant.assistant_id = result.assistant_id_old_to_new[assistant.assistant_id]
                assistant.owner_id = owner_id

                like_expression = re.sub(r"([?%_])", r"\\\1", assistant.name.lower())
                like_expression = f"{like_expression} (%)"
                existing_count = 0
                for possible_match in await session.exec(
                    select(db.Assistant)
                    .where(db.Assistant.owner_id == owner_id)
                    .where(
                        or_(
                            func.lower(col(db.Assistant.name)).like(like_expression),
                            func.lower(col(db.Assistant.name)) == assistant.name.lower(),
                        )
                    )
                ):
                    if possible_match.name.lower() == assistant.name.lower():
                        existing_count += 1
                        continue
                    name = possible_match.name.lower().replace(assistant.name.lower(), "", 1)
                    if re.match(r"^ \(\d+\)$", name):
                        existing_count += 1

                if existing_count > 0:
                    assistant.name = f"{assistant.name} ({existing_count})"

                session.add(assistant)

            case db.AssistantParticipant.__name__:
                participant = db.AssistantParticipant.model_validate(record.data)
                result.assistant_conversation_old_ids[participant.assistant_id].add(participant.conversation_id)
                conversation_id = result.conversation_id_old_to_new.get(participant.conversation_id)
                if conversation_id is None:
                    raise RuntimeError(f"conversation_id {participant.conversation_id} is not found")
                assistant_id = result.assistant_id_old_to_new.get(participant.assistant_id)
                if assistant_id is None:
                    raise RuntimeError(f"assistant_id {participant.assistant_id} is not found")
                participant.conversation_id = conversation_id
                participant.assistant_id = assistant_id
                participant.status = None
                session.add(participant)

            case db.User.__name__:
                user = db.User.model_validate(record.data)
                await db.insert_if_not_exists(session, user)

            case db.UserParticipant.__name__:
                participant = db.UserParticipant.model_validate(record.data)
                conversation_id = result.conversation_id_old_to_new.get(participant.conversation_id)
                if conversation_id is None:
                    raise RuntimeError(f"conversation_id {participant.conversation_id} is not found")
                participant.conversation_id = conversation_id
                # user participants should always be inactive on import
                participant.active_participant = False
                participant.status = None
                session.add(participant)

            case db.Conversation.__name__:
                conversation = db.Conversation.model_validate(record.data)
                result.conversation_id_old_to_new[conversation.conversation_id] = uuid.uuid4()
                conversation.conversation_id = result.conversation_id_old_to_new[conversation.conversation_id]
                conversation.created_datetime = datetime.datetime.utcnow()
                conversation.owner_id = owner_id

                like_expression = re.sub(r"([?%_])", r"\\\1", conversation.title.lower())
                like_expression = f"{like_expression} (%)"
                existing_count = 0
                for possible_match in await session.exec(
                    select(db.Conversation)
                    .where(db.Conversation.owner_id == owner_id)
                    .where(
                        or_(
                            func.lower(col(db.Conversation.title)).like(like_expression),
                            func.lower(col(db.Conversation.title)) == conversation.title.lower(),
                        )
                    )
                ):
                    if possible_match.title.lower() == conversation.title.lower():
                        existing_count += 1
                        continue

                    name = possible_match.title.lower().replace(conversation.title.lower(), "", 1)
                    if re.match(r"^ \(\d+\)$", name):
                        existing_count += 1

                if existing_count > 0:
                    conversation.title = f"{conversation.title} ({existing_count})"

                session.add(conversation)

            case db.ConversationMessage.__name__:
                record.data.pop("sequence", None)
                message = db.ConversationMessage.model_validate(record.data)
                conversation_id = result.conversation_id_old_to_new.get(message.conversation_id)
                if conversation_id is None:
                    raise RuntimeError(f"conversation_id {message.conversation_id} is not found")
                message.conversation_id = conversation_id
                message.message_id = uuid.uuid4()

                if message.sender_participant_role == "assistant":
                    assistant_id = result.assistant_id_old_to_new.get(uuid.UUID(message.sender_participant_id))
                    if assistant_id is None:
                        raise RuntimeError(f"assistant_id {message.sender_participant_id} is not found")
                    message.sender_participant_id = str(assistant_id)
                session.add(message)

    for file in files:
        for line in iter(lambda: file.readline(), b""):
            record = _Record.model_validate_json(line.decode("utf-8"))
            await _process_record(record)
            await session.flush()

    return result
