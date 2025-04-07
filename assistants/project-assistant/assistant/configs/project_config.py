from typing import Annotated

from pydantic import BaseModel, ConfigDict, Field
from semantic_workbench_assistant.config import UISchema


class RequestConfig(BaseModel):
    model_config = ConfigDict(
        title="Response Generation",
        json_schema_extra={
            "required": ["max_tokens", "response_tokens", "openai_model"],
        },
    )

    max_tokens: Annotated[
        int,
        Field(
            title="Max Tokens",
            description=(
                "The maximum number of tokens to use for both the prompt and response. Current max supported by OpenAI"
                " is 128k tokens, but varies by model (https://platform.openai.com/docs/models)"
            ),
        ),
    ] = 50_000

    response_tokens: Annotated[
        int,
        Field(
            title="Response Tokens",
            description=(
                "The number of tokens to use for the response, will reduce the number of tokens available for the"
                " prompt. Current max supported by OpenAI is 4096 tokens (https://platform.openai.com/docs/models)"
            ),
        ),
    ] = 4_048

    openai_model: Annotated[
        str,
        Field(title="OpenAI Model", description="The OpenAI model to use for generating responses."),
    ] = "gpt-4o"


class SenderConfig(BaseModel):
    model_config = ConfigDict(
        title="Project Sender Configuration",
        json_schema_extra={
            "required": ["welcome_message", "prompt_for_files", "context_building_prompt"],
        },
    )

    welcome_message: Annotated[
        str,
        Field(
            title="Sender Welcome Message",
            description="The message to display when a project coordinator starts a new conversation.",
        ),
        UISchema(widget="textarea"),
    ] = "Welcome to your project control! As the project coordinator, I'll help you build context by organizing files and information to share with your team. You can upload files, invite team members with the /invite command, and I'll help synchronize everything between conversations."

    prompt_for_files: Annotated[
        str,
        Field(
            title="File Upload Prompt",
            description="The message used to prompt project coordinators to upload relevant files.",
        ),
        UISchema(widget="textarea"),
    ] = "To begin building your project context, would you like to upload any relevant files like documents, images, or data that your team will need? You can drag and drop files directly into this conversation."

    context_building_prompt: Annotated[
        str,
        Field(
            title="Context Building Prompt",
            description="The message used to help project coordinators organize their project context.",
        ),
        UISchema(widget="textarea"),
    ] = "Let's organize your project context. Here are some ways to structure your information:\n\n- Key documents: What reference materials does your team need?\n- Project objectives: What are the specific goals and deliverables?\n- Timeline: What are the key milestones and deadlines?\n- Team roles: Who should do what?\n\nWould you like me to help you document any of these aspects?"

    list_participants_command: Annotated[
        str,
        Field(
            title="List Participants Command",
            description="The command project coordinators can use to list all participants (without the slash).",
        ),
    ] = "list-participants"

    revoke_access_command: Annotated[
        str,
        Field(
            title="Revoke Access Command",
            description="The command project coordinators can use to revoke access for a participant (without the slash).",
        ),
    ] = "revoke"


class ReceiverConfig(BaseModel):
    model_config = ConfigDict(
        title="Project Receiver Configuration",
        json_schema_extra={
            "required": ["welcome_message", "status_command"],
        },
    )

    welcome_message: Annotated[
        str,
        Field(
            title="Receiver Welcome Message",
            description="The message to display when a user joins a project via invitation.",
        ),
        UISchema(widget="textarea"),
    ] = "Welcome to the project! You've been added as a collaborator, and any files shared by the project coordinator will appear in this conversation. You can also contribute by uploading your own files, which will be shared with the team."

    status_command: Annotated[
        str,
        Field(
            title="Status Command",
            description="The command project participants can use to check project status (without the slash).",
        ),
    ] = "project-status"

    upload_notification: Annotated[
        str,
        Field(
            title="Upload Notification",
            description="The message displayed when a project team member uploads a file.",
        ),
        UISchema(widget="textarea"),
    ] = "Your file has been uploaded and shared with the project team. The project coordinator and other participants will be notified."


class ProjectConfig(BaseModel):
    model_config = ConfigDict(
        title="Project Configuration",
        json_schema_extra={
            "required": ["auto_sync_files", "invite_command", "join_command"],
        },
    )

    auto_sync_files: Annotated[
        bool,
        Field(
            title="Auto-sync Files",
            description="Automatically synchronize files between linked conversations.",
        ),
    ] = True

    invite_command: Annotated[
        str,
        Field(
            title="Invite Command",
            description="The command users can type to invite others (without the slash).",
        ),
    ] = "invite"

    join_command: Annotated[
        str,
        Field(
            title="Join Command",
            description="The command users can type to join a project (without the slash).",
        ),
    ] = "join"

    invitation_message: Annotated[
        str,
        Field(
            title="Invitation Message",
            description="The message sent to users when they are invited to collaborate.",
        ),
        UISchema(widget="textarea"),
    ] = "You've been invited to collaborate on a project. Type /join to accept the invitation."

    proactive_guidance: Annotated[
        bool,
        Field(
            title="Proactive Guidance",
            description="Proactively guide project coordinators through context building.",
        ),
    ] = True

    sender_config: Annotated[
        SenderConfig,
        Field(
            title="Sender Configuration",
            description="Configuration for project coordinators (senders).",
        ),
    ] = SenderConfig()

    receiver_config: Annotated[
        ReceiverConfig,
        Field(
            title="Receiver Configuration",
            description="Configuration for project team members (receivers).",
        ),
    ] = ReceiverConfig()
