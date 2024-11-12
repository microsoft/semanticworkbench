import logging

from chat_driver import ChatDriver, ChatDriverConfig, ContextProtocol
from chat_driver.in_memory_message_history_provider import InMemoryMessageHistoryProvider
from openai import AsyncAzureOpenAI, AsyncOpenAI

logger = logging.getLogger(__name__)

SYSTEM_TEMPLATE = """You are a helpful, thoughtful, and meticulous assistant. You are conducting a conversation with a user. Your goal is to complete an artifact as thoroughly as possible by the end of the conversation.

You will be given some reasoning about the best possible action(s) to take next given the state of the conversation as well as the artifact schema.

The reasoning is supposed to state the recommended action(s) to take next, along with all required parameters for each action.

Your task is to execute ALL actions recommended in the reasoning in the order they are listed.
If the reasoning's specification of an action is incomplete (e.g. it doesn't include all required parameters for the action, or some parameters are specified implicitly, such as "send a message that contains a greeting" instead of explicitly providing the value of the "message" parameter), do not execute the action. You should never fill in missing or imprecise
parameters yourself.

If the reasoning is not clear about which actions to take, or all actions are specified in an incomplete way, return 'None' without selecting any action."""

USER_TEMPLATE = """Artifact schema:
{{ artifact_schema }}

If the type in the schema is str, the "field_value" parameter in the action should be also be a string.
These are example parameters for the update_artifact action: {"field_name": "company_name", "field_value": "Contoso"}
DO NOT write JSON in the "field_value" parameter in this case.
{"field_name": "company_name", "field_value": "{"value": "Contoso"}"} is INCORRECT.

Reasoning:
{{ reasoning }}"""


async def execute_reasoning(
    context: ContextProtocol,
    open_ai_client: AsyncOpenAI | AsyncAzureOpenAI,
    reasoning: str,
    artifact_schema: str,
):
    history = InMemoryMessageHistoryProvider()

    history.append_system_message(
        SYSTEM_TEMPLATE,
    )
    history.append_user_message(
        USER_TEMPLATE,
        {
            "artifact_schema": artifact_schema,
            "reasoning": reasoning,
        },
    )

    config = ChatDriverConfig(
        openai_client=open_ai_client,
        model="gpt-3.5-turbo",
        message_provider=history,
    )

    chat_driver = ChatDriver(config)
    return await chat_driver.respond()
