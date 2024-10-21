import uuid
from typing import Iterable, Mapping

from semantic_workbench_api_model.workbench_model import (
    Assistant,
    AssistantList,
    AssistantServiceRegistration,
    AssistantServiceRegistrationList,
    Conversation,
    ConversationList,
    ConversationMessage,
    ConversationMessageList,
    ConversationParticipant,
    ConversationParticipantList,
    ConversationPermission,
    ConversationShare,
    ConversationShareList,
    ConversationShareRedemption,
    ConversationShareRedemptionList,
    File,
    FileList,
    FileVersion,
    FileVersions,
    MessageSender,
    MessageType,
    ParticipantRole,
    User,
    UserList,
    WorkflowDefinition,
    WorkflowDefinitionList,
    WorkflowParticipant,
    WorkflowRun,
    WorkflowRunList,
)

from .. import db


def user_from_db(model: db.User) -> User:
    return User(
        id=model.user_id,
        name=model.name,
        image=model.image,
        service_user=model.service_user,
        created_datetime=model.created_datetime,
    )


def user_list_from_db(models: Iterable[db.User]) -> UserList:
    return UserList(users=[user_from_db(model) for model in models])


def assistant_service_registration_from_db(
    model: db.AssistantServiceRegistration,
    include_api_key_name: bool,
    api_key: str | None = None,
) -> AssistantServiceRegistration:
    return AssistantServiceRegistration(
        assistant_service_id=model.assistant_service_id,
        created_by_user_id=model.created_by_user_id,
        created_by_user_name=model.related_created_by_user.name,
        created_datetime=model.created_datetime,
        name=model.name,
        description=model.description,
        include_in_listing=model.include_in_listing,
        api_key_name=model.api_key_name if include_api_key_name else "",
        api_key=api_key,
        assistant_service_url=model.assistant_service_url,
        assistant_service_online=model.assistant_service_online,
        assistant_service_online_expiration_datetime=model.assistant_service_online_expiration_datetime,
    )


def assistant_service_registration_list_from_db(
    models: Iterable[db.AssistantServiceRegistration], include_api_key_name: bool
) -> AssistantServiceRegistrationList:
    return AssistantServiceRegistrationList(
        assistant_service_registrations=[
            assistant_service_registration_from_db(model=a, include_api_key_name=include_api_key_name) for a in models
        ]
    )


def assistant_from_db(
    model: db.Assistant,
) -> Assistant:
    return Assistant(
        id=model.assistant_id,
        name=model.name,
        image=model.image,
        metadata=model.meta_data,
        assistant_service_id=model.assistant_service_id,
        created_datetime=model.created_datetime,
    )


def assistant_list_from_db(
    models: Iterable[db.Assistant],
) -> AssistantList:
    return AssistantList(assistants=[assistant_from_db(model=a) for a in models])


def conversation_participant_from_db_user(model: db.UserParticipant) -> ConversationParticipant:
    return ConversationParticipant(
        role=ParticipantRole.service if model.service_user else ParticipantRole.user,
        id=model.user_id,
        conversation_id=model.conversation_id,
        name=model.name,
        image=model.image,
        status=model.status,
        status_updated_timestamp=model.status_updated_datetime,
        active_participant=model.active_participant,
        conversation_permission=ConversationPermission(model.conversation_permission),
    )


def conversation_participant_from_db_assistant(
    model: db.AssistantParticipant, assistant: db.Assistant | None
) -> ConversationParticipant:
    return ConversationParticipant(
        role=ParticipantRole.assistant,
        id=str(model.assistant_id),
        conversation_id=model.conversation_id,
        name=model.name,
        image=model.image,
        status=model.status,
        status_updated_timestamp=model.status_updated_datetime,
        active_participant=model.active_participant,
        online=assistant.related_assistant_service_registration.assistant_service_online if assistant else False,
        conversation_permission=ConversationPermission.read_write,
    )


def conversation_participant_list_from_db(
    user_participants: Iterable[db.UserParticipant],
    assistant_participants: Iterable[db.AssistantParticipant],
    assistants: Mapping[uuid.UUID, db.Assistant],
) -> ConversationParticipantList:
    return ConversationParticipantList(
        participants=[conversation_participant_from_db_user(model=p) for p in user_participants]
        + [
            conversation_participant_from_db_assistant(model=p, assistant=assistants.get(p.assistant_id))
            for p in assistant_participants
        ]
    )


def conversation_from_db(
    model: db.Conversation,
    permission: str,
) -> Conversation:
    return Conversation(
        id=model.conversation_id,
        title=model.title,
        owner_id=model.owner_id,
        imported_from_conversation_id=model.imported_from_conversation_id,
        metadata=model.meta_data,
        created_datetime=model.created_datetime,
        conversation_permission=ConversationPermission(permission),
    )


def conversation_list_from_db(
    models: Iterable[db.Conversation], permissions: Mapping[uuid.UUID, str]
) -> ConversationList:
    return ConversationList(
        conversations=[conversation_from_db(model=m, permission=permissions[m.conversation_id]) for m in models]
    )


def conversation_share_from_db(model: db.ConversationShare) -> ConversationShare:
    return ConversationShare(
        id=model.conversation_share_id,
        created_by_user=user_from_db(model.related_owner),
        conversation_id=model.conversation_id,
        conversation_title=model.related_conversation.title,
        owner_id=model.owner_id,
        conversation_permission=ConversationPermission(model.conversation_permission),
        is_redeemable=model.is_redeemable,
        created_datetime=model.created_datetime,
        label=model.label,
        metadata=model.meta_data,
    )


def conversation_share_list_from_db(models: Iterable[db.ConversationShare]) -> ConversationShareList:
    return ConversationShareList(conversation_shares=[conversation_share_from_db(model=m) for m in models])


def conversation_share_redemption_from_db(model: db.ConversationShareRedemption) -> ConversationShareRedemption:
    return ConversationShareRedemption(
        id=model.conversation_share_redemption_id,
        redeemed_by_user=user_from_db(model.related_redeemed_by_user),
        conversation_share_id=model.conversation_share_id,
        conversation_permission=ConversationPermission(model.conversation_permission),
        conversation_id=model.conversation_id,
        created_datetime=model.created_datetime,
        new_participant=model.new_participant,
    )


def conversation_share_redemption_list_from_db(
    models: Iterable[db.ConversationShareRedemption],
) -> ConversationShareRedemptionList:
    return ConversationShareRedemptionList(
        conversation_share_redemptions=[conversation_share_redemption_from_db(model=m) for m in models]
    )


def conversation_message_from_db(model: db.ConversationMessage) -> ConversationMessage:
    return ConversationMessage(
        id=model.message_id,
        sender=MessageSender(
            participant_id=model.sender_participant_id,
            participant_role=ParticipantRole(model.sender_participant_role),
        ),
        timestamp=model.created_datetime,
        message_type=MessageType(model.message_type),
        content=model.content,
        content_type=model.content_type,
        metadata=model.meta_data,
        filenames=model.filenames,
    )


def conversation_message_list_from_db(
    models: Iterable[db.ConversationMessage],
) -> ConversationMessageList:
    return ConversationMessageList(messages=[conversation_message_from_db(m) for m in models])


def file_from_db(models: tuple[db.File, db.FileVersion]) -> File:
    file, version = models
    return File(
        conversation_id=file.conversation_id,
        filename=file.filename,
        current_version=file.current_version,
        content_type=version.content_type,
        file_size=version.file_size,
        participant_id=version.participant_id,
        participant_role=ParticipantRole(version.participant_role),
        metadata=version.meta_data,
        created_datetime=file.created_datetime,
        updated_datetime=version.created_datetime,
    )


def file_list_from_db(models: Iterable[tuple[db.File, db.FileVersion]]) -> FileList:
    return FileList(files=[file_from_db(m) for m in models])


def file_version_from_db(model: db.FileVersion) -> FileVersion:
    return FileVersion(
        version=model.version,
        content_type=model.content_type,
        file_size=model.file_size,
        metadata=model.meta_data,
    )


def file_versions_from_db(file: db.File, versions: Iterable[db.FileVersion]) -> FileVersions:
    return FileVersions(
        conversation_id=file.conversation_id,
        filename=file.filename,
        created_datetime=file.created_datetime,
        current_version=file.current_version,
        versions=[file_version_from_db(v) for v in versions],
    )


def workflow_definition_from_db(model: db.WorkflowDefinition) -> WorkflowDefinition:
    return WorkflowDefinition.model_validate({
        "id": model.workflow_definition_id,
        **model.data,
    })


def workflow_definition_list_from_db(models: Iterable[db.WorkflowDefinition]) -> WorkflowDefinitionList:
    return WorkflowDefinitionList(workflow_definitions=[workflow_definition_from_db(model) for model in models])


def workflow_participant_from_db(model: db.WorkflowUserParticipant) -> WorkflowParticipant:
    return WorkflowParticipant(
        id=model.user_id,
        active_participant=model.active_participant,
    )


def workflow_run_from_db(model: db.WorkflowRun) -> WorkflowRun:
    return WorkflowRun(
        id=model.workflow_run_id,
        workflow_definition_id=model.workflow_definition_id,
        **model.data,
    )


def workflow_run_list_from_db(models: Iterable[db.WorkflowRun]) -> WorkflowRunList:
    return WorkflowRunList(workflow_runs=[workflow_run_from_db(model) for model in models])
