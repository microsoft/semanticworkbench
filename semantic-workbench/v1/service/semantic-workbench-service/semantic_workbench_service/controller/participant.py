import uuid
from typing import Literal

from semantic_workbench_api_model.workbench_model import (
    ConversationEvent,
    ConversationEventType,
    ConversationParticipant,
    ConversationParticipantList,
)
from sqlmodel import col, select
from sqlmodel.ext.asyncio.session import AsyncSession

from .. import db
from . import convert


async def get_conversation_participants(
    session: AsyncSession, conversation_id: uuid.UUID, include_inactive: bool
) -> ConversationParticipantList:
    user_query = select(db.UserParticipant).where(db.UserParticipant.conversation_id == conversation_id)
    assistant_query = select(db.AssistantParticipant).where(db.AssistantParticipant.conversation_id == conversation_id)

    if not include_inactive:
        user_query = user_query.where(col(db.UserParticipant.active_participant).is_(True))
        assistant_query = assistant_query.where(col(db.AssistantParticipant.active_participant).is_(True))

    user_results = (await session.exec(user_query)).all()
    assistant_results = (await session.exec(assistant_query)).all()

    assistant_ids = {p.assistant_id for p in assistant_results}
    assistants = (
        await session.exec(select(db.Assistant).where(col(db.Assistant.assistant_id).in_(assistant_ids)))
    ).all()
    assistant_map = {a.assistant_id: a for a in assistants}

    return convert.conversation_participant_list_from_db(
        user_participants=user_results, assistant_participants=assistant_results, assistants=assistant_map
    )


def participant_event(
    event_type: Literal[
        ConversationEventType.participant_created,
        ConversationEventType.participant_updated,
        ConversationEventType.participant_deleted,
    ],
    conversation_id: uuid.UUID,
    participant: ConversationParticipant,
    participants: ConversationParticipantList,
) -> ConversationEvent:
    return ConversationEvent(
        conversation_id=conversation_id,
        event=event_type,
        data={
            "participant": participant.model_dump(),
            **participants.model_dump(),
        },
    )
