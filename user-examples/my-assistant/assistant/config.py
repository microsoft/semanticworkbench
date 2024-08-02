from typing import Annotated
from openai_assistant import openai_chat
from pydantic import BaseModel, Field

from assistant.agents.attachment_agent import AttachmentAgentConfigModel, attachment_agent_config_ui_schema


class AgentsConfigModel(BaseModel):
    attachment_agent: Annotated[
        AttachmentAgentConfigModel,
        Field(
            title="Attachment Agent Configuration",
            description="Configuration for the attachment agent.",
        ),
    ] = AttachmentAgentConfigModel()


class HighTokenUsageWarning(BaseModel):
    enabled: Annotated[
        bool,
        Field(
            title="Enabled",
            description="Whether to warn when the assistant's token usage is high.",
        ),
    ] = True

    message: Annotated[
        str,
        Field(
            title="Message",
            description="The message to display when the assistant's token usage is high.",
        ),
    ] = (
        "The assistant's token usage is high. If there are attachments that are no longer needed, you can delete them"
        " to free up tokens."
    )

    threshold: Annotated[
        int,
        Field(
            title="Threshold",
            description="The threshold percentage at which to warn about high token usage.",
        ),
    ] = 90


class AssistantConfigModel(openai_chat.OpenAIChatConfigModel):
    persona_prompt: Annotated[
        str,
        Field(
            title="Persona Prompt",
            description="The prompt used to define the persona of the AI assistant.",
        ),
    ] = (
        "You are an AI assistant that helps users synthesize information from conversations and documents to create"
        " a shared understanding of complex topics. Focus on assisting the user and"
        " drawing out the info needed in order to bring clarity to the topic at hand."
    )

    welcome_message: Annotated[
        str,
        Field(
            title="Welcome Message",
            description="The message to display when the assistant is started.",
        ),
    ] = (
        'Hello! I am a "co-intelligence" assistant that can help you synthesize information from conversations and'
        " documents to create a shared understanding of complex topics. Let's get started by having a conversation!"
        " You can also attach .docx, text, and image files to your chat messages to help me better understand the"
        " context of our conversation. Where would you like to start?"
    )

    high_token_usage_warning: Annotated[
        HighTokenUsageWarning,
        Field(
            title="High Token Usage Warning",
            description="Configuration for the high token usage warning.",
        ),
    ] = HighTokenUsageWarning()

    agents_config: Annotated[
        AgentsConfigModel,
        Field(
            title="Agents Configuration",
            description="Configuration for the assistant agents.",
        ),
    ] = AgentsConfigModel()


assistant_config_ui_schema = {
    **openai_chat.openai_chat_config_ui_schema,
    "welcome_message": {
        "ui:widget": "textarea",
    },
    "agents_config": {
        "attachment_agent": attachment_agent_config_ui_schema,
    },
    "high_token_usage_warning": {
        "message": {
            "ui:widget": "textarea",
        },
    },
}
