from textwrap import dedent

from assistant_extensions.mcp import MCPSession, get_mcp_server_prompts
from openai_client import OpenAIRequestConfig
from semantic_workbench_api_model.workbench_model import ConversationMessage, ConversationParticipant
from semantic_workbench_assistant.assistant_app import ConversationContext

from ..config import AssistantConfigModel
from .local_tool.list_assistant_services import get_assistant_services
from .models import SILENCE_TOKEN


def conditional(condition: bool, content: str) -> str:
    """
    Generate a system message prompt based on a condition.
    """

    if condition:
        return content

    return ""


def combine(*parts: str) -> str:
    return "\n\n".join((part.strip() for part in parts if part.strip()))


def participants_system_prompt(context: ConversationContext, participants: list[ConversationParticipant]) -> str:
    """
    Generate a system message prompt based on the participants in the conversation.
    """

    participant_names = ", ".join([
        f'"{participant.name}"' for participant in participants if participant.id != context.assistant.id
    ])
    system_message_content = dedent(f"""
        There are {len(participants)} participants in the conversation,
        including you as the assistant, with the name {context.assistant.name}, and the following users: {participant_names}.
        \n\n
        You do not need to respond to every message. Do not respond if the last thing said was a closing
        statement such as "bye" or "goodbye", or just a general acknowledgement like "ok" or "thanks". Do not
        respond as another user in the conversation, only as "{context.assistant.name}".
        \n\n
        Say "{SILENCE_TOKEN}" to skip your turn.
    """).strip()

    return system_message_content


async def build_system_message(
    context: ConversationContext,
    config: AssistantConfigModel,
    request_config: OpenAIRequestConfig,
    message: ConversationMessage,
    mcp_sessions: list[MCPSession],
) -> str:
    # Retrieve prompts from the MCP servers
    mcp_prompts = await get_mcp_server_prompts(mcp_sessions)

    participants_response = await context.get_participants()

    assistant_services_list = await get_assistant_services(context)

    return combine(
        conditional(
            request_config.is_reasoning_model and request_config.enable_markdown_in_reasoning_response,
            "Formatting re-enabled",
        ),
        combine("# Instructions", config.prompts.instruction_prompt, 'Your name is "{context.assistant.name}".'),
        conditional(
            len(participants_response.participants) > 2 and not message.mentions(context.assistant.id),
            participants_system_prompt(context, participants_response.participants),
        ),
        combine("# Workflow Guidance", config.prompts.guidance_prompt),
        combine("# Safety Guardrails", config.prompts.guardrails_prompt),
        conditional(
            config.tools.enabled,
            combine(
                "# Tool Instructions",
                config.tools.advanced.additional_instructions,
            ),
        ),
        conditional(
            len(mcp_prompts) > 0,
            combine("# Specific Tool Guidance", *mcp_prompts),
        ),
        combine("# Semantic Workbench Guide", config.prompts.semantic_workbench_guide_prompt),
        combine("# Assistant Service List", assistant_services_list),
    )
