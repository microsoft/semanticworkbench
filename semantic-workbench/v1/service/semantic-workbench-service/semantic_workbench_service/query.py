from typing import Any

from sqlalchemy import Function, func
from sqlmodel import String, and_, cast, col, or_, select
from sqlmodel.sql.expression import SelectOfScalar

from . import auth, db, settings


def json_extract_path(expression, *paths: str) -> Function[Any]:
    if settings.db.url.startswith("sqlite"):
        return func.json_extract(expression, f"$.{'.'.join(paths)}")
    return func.json_extract_path(expression, *paths)


def select_assistants_for(
    user_principal: auth.UserPrincipal, include_assistants_from_conversations: bool = False
) -> SelectOfScalar[db.Assistant]:
    return select(db.Assistant).where(
        or_(
            db.Assistant.owner_id == user_principal.user_id,
            col(db.Assistant.assistant_id).in_(
                select(db.Assistant.assistant_id)
                .join(
                    db.WorkflowRun,
                    cast(json_extract_path(db.Assistant.meta_data, "workflow_run_id"), String)
                    == cast(db.WorkflowRun.workflow_run_id, String),
                )
                .join(
                    db.WorkflowUserParticipant,
                    and_(
                        db.WorkflowUserParticipant.workflow_definition_id == db.WorkflowRun.workflow_definition_id,
                        db.WorkflowUserParticipant.user_id == user_principal.user_id,
                    ),
                )
                .distinct()
            ),
            and_(
                include_assistants_from_conversations is True,
                col(db.Assistant.assistant_id).in_(
                    select(db.AssistantParticipant.assistant_id)
                    .join(
                        db.Conversation,
                        and_(
                            col(db.Conversation.conversation_id) == col(db.AssistantParticipant.conversation_id),
                            col(db.AssistantParticipant.active_participant).is_(True),
                        ),
                    )
                    .join(
                        db.UserParticipant,
                        and_(
                            col(db.UserParticipant.conversation_id) == col(db.Conversation.conversation_id),
                            col(db.UserParticipant.user_id) == user_principal.user_id,
                            col(db.UserParticipant.active_participant).is_(True),
                        ),
                    )
                    .distinct()
                ),
            ),
        )
    )


def select_conversations_for(
    principal: auth.ActorPrincipal,
    include_all_owned: bool = False,
    include_observer: bool = False,
) -> SelectOfScalar[db.Conversation]:
    query = select(db.Conversation)

    if isinstance(principal, auth.UserPrincipal):
        query = query.join(db.UserParticipant).where(db.UserParticipant.user_id == principal.user_id)

        clause = col(db.UserParticipant.active_participant).is_(True)
        if include_all_owned:
            clause = or_(clause, db.Conversation.owner_id == principal.user_id)

        query = query.where(clause)

        if not include_observer:
            query = query.where(db.UserParticipant.conversation_permission != "read")

        return query

    query = (
        query.join(db.AssistantParticipant)
        .where(db.AssistantParticipant.assistant_id == principal.assistant_id)
        .where(col(db.AssistantParticipant.active_participant).is_(True))
    )

    return query


def select_conversation_messages_for(principal: auth.ActorPrincipal) -> SelectOfScalar[db.ConversationMessage]:
    if isinstance(principal, auth.UserPrincipal):
        return (
            select(db.ConversationMessage)
            .join(db.Conversation)
            .join(db.UserParticipant)
            .where(db.UserParticipant.user_id == principal.user_id)
        )
    return (
        select(db.ConversationMessage)
        .join(db.Conversation)
        .join(db.AssistantParticipant)
        .where(db.AssistantParticipant.assistant_id == principal.assistant_id)
    )


def select_workflow_definitions_for(
    user_principal: auth.UserPrincipal,
    include_inactive: bool = False,
) -> SelectOfScalar[db.WorkflowDefinition]:
    query = (
        select(db.WorkflowDefinition)
        .join(db.WorkflowUserParticipant)
        .where(db.WorkflowUserParticipant.user_id == user_principal.user_id)
    )
    if not include_inactive:
        query = query.where(col(db.WorkflowUserParticipant.active_participant).is_(True))

    return query


def select_workflow_runs_for(
    user_principal: auth.UserPrincipal,
    include_inactive: bool = False,
) -> SelectOfScalar[db.WorkflowRun]:
    query = (
        select(db.WorkflowRun)
        .join(db.WorkflowDefinition)
        .join(db.WorkflowUserParticipant)
        .where(db.WorkflowUserParticipant.user_id == user_principal.user_id)
    )
    if not include_inactive:
        query = query.where(col(db.WorkflowUserParticipant.active_participant).is_(True))

    return query
