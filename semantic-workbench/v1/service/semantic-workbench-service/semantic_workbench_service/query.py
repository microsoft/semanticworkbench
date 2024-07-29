from typing import Any

from sqlalchemy import Function, func
from sqlmodel import String, and_, cast, col, select
from sqlmodel.sql.expression import SelectOfScalar

from . import auth, db, service_user_principals, settings


def json_extract_path(expression, *paths: str) -> Function[Any]:
    if settings.db.url.startswith("sqlite"):
        return func.json_extract(expression, f"$.{'.'.join(paths)}")
    return func.json_extract_path(expression, *paths)


def select_assistants_for(user_principal: auth.UserPrincipal) -> SelectOfScalar[db.Assistant]:
    return select(db.Assistant).where(
        col(db.Assistant.assistant_id).in_(
            select(db.Assistant.assistant_id)
            .join(
                db.WorkflowRun,
                cast(json_extract_path(db.Assistant.meta_data, "workflow_run_id"), String)
                == cast(db.WorkflowRun.workflow_run_id, String),
                isouter=True,
            )
            .join(
                db.WorkflowUserParticipant,
                and_(
                    db.WorkflowUserParticipant.workflow_definition_id == db.WorkflowRun.workflow_definition_id,
                    db.WorkflowUserParticipant.user_id == user_principal.user_id,
                ),
                isouter=True,
            )
            .where(col(db.Assistant.owner_id).in_((user_principal.user_id, service_user_principals.workflow.user_id)))
            .distinct()
        )
    )


def select_conversations_for(
    principal: auth.ActorPrincipal,
    include_inactive: bool = False,
) -> SelectOfScalar[db.Conversation]:
    query = select(db.Conversation)

    if isinstance(principal, auth.UserPrincipal):
        query = query.join(db.UserParticipant).where(db.UserParticipant.user_id == principal.user_id)

        if not include_inactive:
            query = query.where(col(db.UserParticipant.active_participant).is_(True))

        return query

    query = query.join(db.AssistantParticipant).where(db.AssistantParticipant.assistant_id == principal.assistant_id)

    if not include_inactive:
        query = query.where(col(db.AssistantParticipant.active_participant).is_(True))

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
    return query
    return query
