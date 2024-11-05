import logging
from typing import Awaitable, Callable, Sequence

from openai.types.chat import ChatCompletionMessageParam
from semantic_workbench_api_model.workbench_model import MessageType, NewConversationMessage
from semantic_workbench_assistant.assistant_app.context import ConversationContext
from semantic_workbench_assistant.assistant_app.protocol import AssistantAppProtocol

from . import state
from .config import FormFillAgentConfig
from .steps import acquire_form_step, extract_form_fields_step, fill_form_step
from .steps.types import ConfigT, Context, IncompleteErrorResult, IncompleteResult, LLMConfig

logger = logging.getLogger(__name__)


async def execute(
    context: ConversationContext,
    llm_config: LLMConfig,
    config: FormFillAgentConfig,
    latest_user_message: str | None,
    get_attachment_messages: Callable[[Sequence[str]], Awaitable[Sequence[ChatCompletionMessageParam]]],
) -> None:
    user_messages = [latest_user_message]

    def build_step_context(config: ConfigT) -> Context[ConfigT]:
        return Context(
            context=context, llm_config=llm_config, config=config, get_attachment_messages=get_attachment_messages
        )

    async with state.agent_state(context) as agent_state:
        while True:
            logger.info("form-fill-agent execute loop; mode: %s", agent_state.mode)

            match agent_state.mode:
                case state.FormFillAgentMode.acquire_form_step:
                    result = await acquire_form_step.execute(
                        step_context=build_step_context(config.acquire_form_config),
                        latest_user_message=user_messages.pop() if user_messages else None,
                    )

                    match result:
                        case acquire_form_step.CompleteResult():
                            await _send_message(context, result.ai_message, result.debug)

                            agent_state.form_filename = result.filename
                            agent_state.mode = state.FormFillAgentMode.extract_form_fields_step

                        case IncompleteResult() | IncompleteErrorResult():
                            await _handle_incomplete_results(context, result)
                            return

                        case _:
                            raise ValueError(f"Unexpected result: {result}")

                case state.FormFillAgentMode.extract_form_fields_step:
                    result = await extract_form_fields_step.execute(
                        step_context=build_step_context(config.extract_form_fields_config),
                        filename=agent_state.form_filename,
                    )

                    match result:
                        case extract_form_fields_step.CompleteResult():
                            await _send_message(context, result.ai_message, result.debug)

                            agent_state.extracted_form_fields = result.extracted_form_fields
                            agent_state.mode = state.FormFillAgentMode.fill_form_step

                        case IncompleteResult() | IncompleteErrorResult():
                            await _handle_incomplete_results(context, result)
                            return

                        case _:
                            raise ValueError(f"Unexpected result: {result}")

                case state.FormFillAgentMode.fill_form_step:
                    result = await fill_form_step.execute(
                        step_context=build_step_context(config.fill_form_config),
                        latest_user_message=user_messages.pop() if user_messages else None,
                        form_fields=agent_state.extracted_form_fields,
                    )

                    match result:
                        case fill_form_step.CompleteResult():
                            await _send_message(context, result.ai_message, result.debug)

                            agent_state.fill_form_gc_artifact = result.artifact
                            agent_state.mode = state.FormFillAgentMode.generate_filled_form_step

                        case IncompleteResult() | IncompleteErrorResult():
                            await _handle_incomplete_results(context, result)
                            return

                        case _:
                            raise ValueError(f"Unexpected result: {result}")

                case state.FormFillAgentMode.generate_filled_form_step:
                    await _send_message(
                        context, "I'd love to generate the filled-out form now, but it's not yet implemented. :)", {}
                    )
                    return

                case state.FormFillAgentMode.end_conversation:
                    await _send_message(context, "Conversation has ended.", {})
                    return

                case _:
                    raise ValueError(f"Unexpected mode: {state.mode}")


async def _handle_incomplete_results(
    context: ConversationContext, result: IncompleteErrorResult | IncompleteResult
) -> None:
    match result:
        case IncompleteResult():
            await _send_message(context, result.ai_message, result.debug)

        case IncompleteErrorResult():
            await _send_error_message(context, result.error_message, result.debug)

        case _:
            raise ValueError(f"Unexpected incomplete result: {result}")


async def _send_message(context: ConversationContext, message: str, debug: dict) -> None:
    if not message:
        return

    await context.send_messages(
        NewConversationMessage(
            content=message,
            message_type=MessageType.chat,
            metadata={"debug": debug},
        )
    )


async def _send_error_message(context: ConversationContext, message: str, debug: dict) -> None:
    await context.send_messages(
        NewConversationMessage(
            content=message,
            message_type=MessageType.notice,
            metadata={"debug": debug},
        )
    )


def extend(app: AssistantAppProtocol) -> None:
    """
    Extend the assistant app with the form-fill agent inspectors.
    """

    # for agent level state
    app.add_inspector_state_provider(state.inspector.state_id, state.inspector)

    # for step level states
    acquire_form_step.extend(app)
    fill_form_step.extend(app)
