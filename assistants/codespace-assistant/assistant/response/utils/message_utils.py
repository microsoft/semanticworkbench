import logging
from textwrap import dedent

from semantic_workbench_api_model.workbench_model import (
    ConversationParticipant,
)
from semantic_workbench_assistant.assistant_app import ConversationContext

from ...config import PromptsConfigModel

logger = logging.getLogger(__name__)


def build_system_message_content(
    prompts_config: PromptsConfigModel,
    context: ConversationContext,
    participants: list[ConversationParticipant],
    silence_token: str,
    additional_content: list[tuple[str, str]] | None = None,
) -> str:
    """
    Construct the system message content with tool descriptions and instructions.
    """

    system_message_content = f'{prompts_config.instruction_prompt}\n\nYour name is "{context.assistant.name}".'

    if len(participants) > 2:
        participant_names = ", ".join([
            f'"{participant.name}"' for participant in participants if participant.id != context.assistant.id
        ])
        system_message_content += dedent(f"""
            \n\n
            There are {len(participants)} participants in the conversation,
            including you as the assistant and the following users: {participant_names}.
            \n\n
            You do not need to respond to every message. Do not respond if the last thing said was a closing
            statement such as "bye" or "goodbye", or just a general acknowledgement like "ok" or "thanks". Do not
            respond as another user in the conversation, only as "{context.assistant.name}".
            Sometimes the other users need to talk amongst themselves and that is okay. If the conversation seems to
            be directed at you or the general audience, go ahead and respond.
            \n\n
            Say "{silence_token}" to skip your turn.
        """).strip()

    system_message_content += f"\n\n# Workflow Guidance:\n{prompts_config.guidance_prompt}"
    system_message_content += f"\n\n# Safety Guardrails:\n{prompts_config.guardrails_prompt}"

    if additional_content:
        for section in additional_content:
            system_message_content += f"\n\n# {section[0]}:\n{section[1]}"

    return system_message_content
