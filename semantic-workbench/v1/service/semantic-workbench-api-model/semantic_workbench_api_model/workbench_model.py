import datetime
import uuid
from enum import StrEnum
from typing import Annotated, Any, Literal

import asgi_correlation_id
from pydantic import BaseModel, Field, HttpUrl

from . import assistant_model


class User(BaseModel):
    id: str
    name: str
    image: str | None
    service_user: bool
    created_datetime: datetime.datetime


class UserList(BaseModel):
    users: list[User]


class AssistantServiceRegistration(BaseModel):
    assistant_service_id: str
    created_by_user_id: str
    created_by_user_name: str
    created_datetime: datetime.datetime
    name: str
    description: str
    include_in_listing: bool
    api_key_name: str

    assistant_service_url: str | None
    assistant_service_online: bool
    assistant_service_online_expiration_datetime: datetime.datetime | None

    api_key: Annotated[str | None, Field(repr=False)] = None


class AssistantServiceRegistrationList(BaseModel):
    assistant_service_registrations: list[AssistantServiceRegistration]


class Assistant(BaseModel):
    id: uuid.UUID
    name: str
    image: str | None
    assistant_service_id: str
    metadata: dict[str, Any]
    created_datetime: datetime.datetime


class AssistantList(BaseModel):
    assistants: list[Assistant]


class ParticipantRole(StrEnum):
    user = "user"
    assistant = "assistant"
    service = "service"


class ParticipantStatus(BaseModel):
    timestamp: datetime.datetime = Field(default_factory=datetime.datetime.utcnow)
    message: str | None = None


class ConversationParticipant(BaseModel):
    role: ParticipantRole
    id: str
    name: str
    image: str | None
    status: str | None
    status_updated_timestamp: datetime.datetime
    active_participant: bool
    online: bool | None = None


class ConversationParticipantList(BaseModel):
    participants: list[ConversationParticipant]


class Conversation(BaseModel):
    id: uuid.UUID
    title: str
    metadata: dict[str, Any]
    created_datetime: datetime.datetime


class ConversationList(BaseModel):
    conversations: list[Conversation]


class MessageSender(BaseModel):
    participant_role: ParticipantRole
    participant_id: str


class MessageType(StrEnum):
    chat = "chat"
    command = "command"
    command_response = "command-response"
    log = "log"
    note = "note"
    notice = "notice"


class ConversationMessage(BaseModel):
    id: uuid.UUID
    sender: MessageSender
    message_type: MessageType = MessageType.chat
    timestamp: datetime.datetime
    content_type: str
    content: str
    filenames: list[str]
    metadata: dict[str, Any]

    @property
    def command_name(self) -> str:
        if self.message_type != MessageType.command:
            return ""

        return self.content.split(" ", 1)[0]

    @property
    def command_args(self) -> str:
        if self.message_type != MessageType.command:
            return ""

        return "".join(self.content.split(" ", 1)[1:])


class ConversationMessageList(BaseModel):
    messages: list[ConversationMessage]


class File(BaseModel):
    conversation_id: uuid.UUID
    created_datetime: datetime.datetime
    updated_datetime: datetime.datetime
    filename: str
    current_version: int
    content_type: str
    file_size: int
    participant_id: str
    participant_role: ParticipantRole
    metadata: dict[str, Any]


class FileList(BaseModel):
    files: list[File]


class FileVersion(BaseModel):
    version: int
    content_type: str
    file_size: int
    metadata: dict[str, Any]


class FileVersions(BaseModel):
    conversation_id: uuid.UUID
    created_datetime: datetime.datetime
    filename: str
    current_version: int
    versions: list[FileVersion]


class ConversationImportResult(BaseModel):
    conversation_ids: list[uuid.UUID]
    assistant_ids: list[uuid.UUID]


class EditorData(BaseModel):
    position: dict[str, float]


class AssistantData(BaseModel):
    assistant_definition_id: str
    config_data: dict[str, Any]


class OutletPrompts(BaseModel):
    evaluate_transition: str
    context_transfer: str | None = None


class OutletData(BaseModel):
    id: str
    label: str
    prompts: OutletPrompts


class WorkflowState(BaseModel):
    id: str
    label: str
    conversation_definition_id: str
    force_new_conversation_instance: bool | None = None
    assistant_data_list: list[AssistantData]
    editor_data: EditorData
    outlets: list[OutletData]


class WorkflowTransition(BaseModel):
    id: str
    source_outlet_id: str
    target_state_id: str


class ConversationDefinition(BaseModel):
    id: str
    title: str


class AssistantDefinition(BaseModel):
    id: str
    name: str
    assistant_service_id: str


class WorkflowDefinition(BaseModel):
    id: uuid.UUID
    label: str
    start_state_id: str
    states: list[WorkflowState]
    transitions: list[WorkflowTransition]
    conversation_definitions: list[ConversationDefinition]
    assistant_definitions: list[AssistantDefinition]
    context_transfer_instruction: str


class WorkflowDefinitionList(BaseModel):
    workflow_definitions: list[WorkflowDefinition]


class NewWorkflowDefinition(BaseModel):
    label: str
    start_state_id: str
    states: list[WorkflowState]
    transitions: list[WorkflowTransition]
    conversation_definitions: list[ConversationDefinition]
    assistant_definitions: list[AssistantDefinition]
    context_transfer_instruction: str


class UpdateWorkflowDefinition(NewWorkflowDefinition):
    pass


class WorkflowParticipant(BaseModel):
    id: str
    active_participant: bool


class UpdateWorkflowParticipant(BaseModel):
    """
    Update the workflow participant's active status.
    """

    active_participant: bool


class WorkflowConversationMapping(BaseModel):
    conversation_id: str
    conversation_definition_id: str


class WorkflowAssistantMapping(BaseModel):
    assistant_id: str
    assistant_definition_id: str


class WorkflowRun(BaseModel):
    id: uuid.UUID
    title: str
    workflow_definition_id: uuid.UUID
    current_state_id: str
    conversation_mappings: list[WorkflowConversationMapping]
    assistant_mappings: list[WorkflowAssistantMapping]
    metadata: dict[str, Any] | None = None


class WorkflowRunList(BaseModel):
    workflow_runs: list[WorkflowRun]


class NewWorkflowRun(BaseModel):
    workflow_definition_id: uuid.UUID
    title: str
    metadata: dict[str, Any] | None = None


class UpdateWorkflowRun(BaseModel):
    """
    Update the workflow run's title and/or metadata. Leave a field as None to not update it.
    """

    title: str | None = None
    metadata: dict[str, Any] | None = None


class UpdateWorkflowRunMappings(BaseModel):
    """
    Update the workflow run's conversation and/or assistant mappings. Leave a field as None to not update it.
    """

    conversation_mappings: list[WorkflowConversationMapping] | None = None
    assistant_mappings: list[WorkflowAssistantMapping] | None = None


class UpdateUser(BaseModel):
    """
    Update the user's name and/or image. Leave a field as None to not update it.
    """

    name: str | None = None
    image: str | None = None


class NewAssistantServiceRegistration(BaseModel):
    assistant_service_id: Annotated[
        str,
        Field(
            min_length=4,
            pattern=r"^[a-z0-9-\.]+$",
            description="lowercase, alphanumeric, hyphen and dot characters only",
        ),
    ]
    name: Annotated[str, Field(min_length=1)]
    description: str
    include_in_listing: bool = True


class UpdateAssistantServiceRegistration(BaseModel):
    name: str | None = None
    description: str | None = None
    include_in_listing: bool | None = None


class UpdateAssistantServiceRegistrationUrl(BaseModel):
    name: str
    description: str
    url: HttpUrl
    online_expires_in_seconds: float


class NewAssistant(BaseModel):
    assistant_service_id: str
    name: str
    image: str | None = None
    metadata: dict[str, Any] = {}


class UpdateAssistant(BaseModel):
    """
    Update the assistant's name, image, and/or metadata. Leave a field as None to not update it.
    """

    name: str | None = None
    image: str | None = None
    metadata: dict[str, Any] = {}


class AssistantStateEvent(BaseModel):
    state_id: str
    event: Literal["created", "updated", "deleted", "focus"]
    state: assistant_model.StateResponseModel | None


class NewConversation(BaseModel):
    title: str
    metadata: dict[str, Any] = {}


class UpdateConversation(BaseModel):
    """
    Update the conversation's title and/or metadata. Leave a field as None to not update it.
    """

    title: str
    metadata: dict[str, Any] = {}


class NewConversationMessage(BaseModel):
    id: uuid.UUID | None = None
    content: str
    message_type: MessageType = MessageType.chat
    content_type: str = "text/plain"
    filenames: list[str] | None = None
    metadata: dict[str, Any] | None = None


class UpdateParticipant(BaseModel):
    """
    Update the participant's status and/or active status. Leave a field as None to not update it.
    """

    status: str | None = None
    active_participant: bool | None = None


class ConversationEventType(StrEnum):
    message_created = "message.created"
    message_deleted = "message.deleted"
    participant_created = "participant.created"
    participant_updated = "participant.updated"
    participant_deleted = "participant.deleted"
    file_created = "file.created"
    file_updated = "file.updated"
    file_deleted = "file.deleted"
    assistant_state_created = "assistant.state.created"
    assistant_state_updated = "assistant.state.updated"
    assistant_state_deleted = "assistant.state.deleted"
    assistant_state_focus = "assistant.state.focus"
    conversation_created = "conversation.created"
    conversation_updated = "conversation.updated"
    conversation_deleted = "conversation.deleted"


class ConversationEvent(BaseModel):
    id: str = Field(default_factory=lambda: uuid.uuid4().hex)
    correlation_id: str = Field(default_factory=lambda: asgi_correlation_id.correlation_id.get() or "")
    conversation_id: uuid.UUID
    event: ConversationEventType
    timestamp: datetime.datetime = Field(default_factory=datetime.datetime.utcnow)
    data: dict[str, Any] = {}
