import logging
from typing import Awaitable, Callable, Sequence

from openai.types.chat import ChatCompletionMessageParam
from semantic_workbench_api_model.workbench_model import MessageType, NewConversationMessage
from semantic_workbench_assistant.assistant_app.context import ConversationContext

from . import state
from .config import FormFillAgentConfig
from .step import Context, IncompleteErrorResult, IncompleteResult, LLMConfig
from .steps import acquire_form, extract_form_fields, fill_form

logger = logging.getLogger(__name__)


async def execute(
    context: ConversationContext,
    llm_config: LLMConfig,
    config: FormFillAgentConfig,
    latest_user_message: str | None,
    get_attachment_messages: Callable[[Sequence[str]], Awaitable[Sequence[ChatCompletionMessageParam]]],
) -> None:
    user_messages = [latest_user_message]

    async with state.agent_state(context) as agent_state:
        for mode in state.FormFillAgentMode:
            if mode in agent_state.mode_debug_log:
                continue

            agent_state.mode_debug_log[mode] = []

        while True:
            logger.info("form-fill-agent step; mode: %s", agent_state.mode)

            match agent_state.mode:
                case state.FormFillAgentMode.acquire_form_step:
                    step_context = Context(
                        context=context,
                        llm_config=llm_config,
                        config=config.acquire_form_config,
                        get_attachment_messages=get_attachment_messages,
                    )

                    result = await acquire_form.execute(
                        step_context=step_context,
                        latest_user_message=user_messages.pop() if user_messages else None,
                    )

                    agent_state.mode_debug_log[agent_state.mode].insert(0, result.debug)
                    match result:
                        case IncompleteResult():
                            await _send_message(context, result.ai_message, result.debug)
                            return

                        case IncompleteErrorResult():
                            await _send_error_message(context, result.error_message, result.debug)
                            return

                        case acquire_form.CompleteResult():
                            await _send_message(context, result.ai_message, result.debug)

                            agent_state.form_filename = result.filename
                            agent_state.mode = state.FormFillAgentMode.extract_form_fields_step
                            continue

                        case _:
                            raise ValueError(f"Unexpected result: {result}")

                case state.FormFillAgentMode.extract_form_fields_step:
                    step_context = Context(
                        context=context,
                        llm_config=llm_config,
                        config=config.extract_form_fields_config,
                        get_attachment_messages=get_attachment_messages,
                    )

                    result = await extract_form_fields.execute(
                        step_context=step_context,
                        filename=agent_state.form_filename,
                    )

                    agent_state.mode_debug_log[agent_state.mode].insert(0, result.debug)
                    match result:
                        case IncompleteErrorResult():
                            await _send_error_message(context, result.error_message, result.debug)
                            return

                        case IncompleteResult():
                            await _send_message(context, result.ai_message, result.debug)
                            return

                        case extract_form_fields.CompleteResult():
                            await _send_message(context, result.ai_message, result.debug)

                            agent_state.extracted_form_fields = result.extracted_form_fields
                            agent_state.mode = state.FormFillAgentMode.fill_form_step
                            continue

                        case _:
                            raise ValueError(f"Unexpected result: {result}")

                case state.FormFillAgentMode.fill_form_step:
                    step_context = Context(
                        context=context,
                        llm_config=llm_config,
                        config=config.fill_form_config,
                        get_attachment_messages=get_attachment_messages,
                    )

                    result = await fill_form.execute(
                        step_context=step_context,
                        latest_user_message=user_messages.pop() if user_messages else None,
                        form_fields=agent_state.extracted_form_fields,
                    )

                    agent_state.mode_debug_log[agent_state.mode].insert(0, result.debug)
                    match result:
                        case IncompleteResult():
                            await _send_message(context, result.ai_message, result.debug)
                            return

                        case IncompleteErrorResult():
                            await _send_error_message(context, result.error_message, result.debug)
                            return

                        case fill_form.CompleteResult():
                            await _send_message(context, result.ai_message, result.debug)

                            agent_state.fill_form_gc_artifact = result.artifact
                            agent_state.mode = state.FormFillAgentMode.generate_filled_form_step
                            continue

                        case _:
                            raise ValueError(f"Unexpected result: {result}")

                case state.FormFillAgentMode.generate_filled_form_step:
                    await context.send_messages(
                        NewConversationMessage(
                            content="I'd love to generate the fill form now, but it's not yet implemented. :)"
                        )
                    )
                    return

                case state.FormFillAgentMode.end_conversation:
                    await context.send_messages(NewConversationMessage(content="Conversation has ended."))
                    return

                case _:
                    raise ValueError(f"Unexpected mode: {state.mode}")


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
