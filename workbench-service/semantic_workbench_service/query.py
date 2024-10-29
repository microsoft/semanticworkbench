from typing import Any, TypeVar

from sqlalchemy import Function
from sqlmodel import String, and_, cast, col, func, literal, or_, select
from sqlmodel.sql.expression import Select, SelectOfScalar

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


SelectT = TypeVar("SelectT", SelectOfScalar, Select)


def _select_conversations_for(
    principal: auth.ActorPrincipal,
    select_query: SelectT,
    include_all_owned: bool = False,
    include_observer: bool = False,
) -> SelectT:
    match principal:
        case auth.UserPrincipal():
            join_clause = and_(
                db.UserParticipant.conversation_id == db.Conversation.conversation_id,
                db.UserParticipant.user_id == principal.user_id,
            )
            if not include_observer:
                join_clause = and_(join_clause, db.UserParticipant.conversation_permission != "read")

            query = select_query.join_from(db.Conversation, db.UserParticipant, onclause=join_clause)

            where_clause = col(db.UserParticipant.active_participant).is_(True)

            if include_all_owned:
                where_clause = or_(where_clause, db.Conversation.owner_id == principal.user_id)

            query = query.where(where_clause)

            return query

        case auth.AssistantPrincipal():
            query = select_query.join(
                db.AssistantParticipant,
                and_(
                    db.AssistantParticipant.conversation_id == db.Conversation.conversation_id,
                    db.AssistantParticipant.assistant_id == principal.assistant_id,
                    col(db.AssistantParticipant.active_participant).is_(True),
                ),
            )

            return query


def select_conversations_for(
    principal: auth.ActorPrincipal,
    include_all_owned: bool = False,
    include_observer: bool = False,
) -> SelectOfScalar[db.Conversation]:
    return _select_conversations_for(
        principal=principal,
        select_query=select(db.Conversation),
        include_all_owned=include_all_owned,
        include_observer=include_observer,
    )


def select_conversation_projections_for(
    principal: auth.ActorPrincipal,
    include_all_owned: bool = False,
    include_observer: bool = False,
) -> Select[tuple[db.Conversation, db.ConversationMessage | None, str]]:
    latest_message_subquery = (
        select(
            db.ConversationMessage.conversation_id,
            func.max(db.ConversationMessage.sequence).label("latest_message_sequence"),
        )
        .group_by(col(db.ConversationMessage.conversation_id))
        .subquery()
    )

    match principal:
        case auth.UserPrincipal():
            select_query = select(
                db.Conversation,
                db.ConversationMessage,
                db.UserParticipant.conversation_permission,
            )

        case auth.AssistantPrincipal():
            select_query = select(
                db.Conversation,
                db.ConversationMessage,
                literal("read_write").label("conversation_permission"),
            )

    query = _select_conversations_for(
        principal=principal,
        include_all_owned=include_all_owned,
        include_observer=include_observer,
        select_query=select_query,
    )

    return query.join_from(
        db.Conversation,
        latest_message_subquery,
        onclause=col(db.Conversation.conversation_id) == col(latest_message_subquery.c.conversation_id),
        isouter=True,
    ).join_from(
        db.Conversation,
        db.ConversationMessage,
        onclause=and_(
            col(db.Conversation.conversation_id) == col(db.ConversationMessage.conversation_id),
            col(db.ConversationMessage.sequence) == col(latest_message_subquery.c.latest_message_sequence),
        ),
        isouter=True,
    )


def select_conversation_messages_for(principal: auth.ActorPrincipal) -> SelectOfScalar[db.ConversationMessage]:
    match principal:
        case auth.UserPrincipal():
            return (
                select(db.ConversationMessage)
                .join(db.Conversation)
                .join(db.UserParticipant)
                .where(db.UserParticipant.user_id == principal.user_id)
            )

        case auth.AssistantPrincipal():
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
