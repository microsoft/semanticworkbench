import logging
from typing import AsyncIterable, Awaitable, Callable, Sequence

from semantic_workbench_api_model.workbench_model import MessageType, NewConversationMessage
from semantic_workbench_assistant.assistant_app.context import ConversationContext
from semantic_workbench_assistant.assistant_app.protocol import AssistantAppProtocol

from . import state
from .config import FormFillConfig
from .steps import acquire_form_step, extract_form_fields_step, fill_form_step
from .steps.types import ConfigT, Context, IncompleteErrorResult, IncompleteResult, LLMConfig, UserAttachment, UserInput

logger = logging.getLogger(__name__)


class FormFillExtension:
    def __init__(self, assistant_app: AssistantAppProtocol) -> None:
        """
        Extend the assistant app with the form-fill agent inspectors.
        """

        # for agent level state
        assistant_app.add_inspector_state_provider(state.inspector.state_id, state.inspector)

        # for step level states
        acquire_form_step.extend(assistant_app)
        fill_form_step.extend(assistant_app)

    async def execute(
        self,
        context: ConversationContext,
        llm_config: LLMConfig,
        config: FormFillConfig,
        latest_user_message: str | None,
        latest_attachment_filenames: Sequence[str],
        get_attachment_content: Callable[[str], Awaitable[str]],
    ) -> None:
        user_messages = [latest_user_message]

        async def latest_attachments() -> AsyncIterable[UserAttachment]:
            for filename in latest_attachment_filenames:
                content = await get_attachment_content(filename)
                yield UserAttachment(filename=filename, content=content)

        def build_step_context(config: ConfigT) -> Context[ConfigT]:
            return Context(
                context=context,
                llm_config=llm_config,
                config=config,
                latest_user_input=UserInput(
                    message=user_messages.pop() if user_messages else None,
                    attachments=latest_attachments(),
                ),
            )

        async with state.extension_state(context) as agent_state:
            while True:
                logger.info("form-fill-agent execute loop; mode: %s", agent_state.mode)

                match agent_state.mode:
                    case state.FormFillExtensionMode.acquire_form_step:
                        result = await acquire_form_step.execute(
                            step_context=build_step_context(config.acquire_form_config),
                        )

                        match result:
                            case acquire_form_step.CompleteResult():
                                await _send_message(context, result.message, result.debug)

                                agent_state.form_filename = result.filename
                                agent_state.mode = state.FormFillExtensionMode.extract_form_fields

                                continue

                            case _:
                                await _handle_incomplete_result(context, result)
                                return

                    case state.FormFillExtensionMode.extract_form_fields:
                        file_content = await get_attachment_content(agent_state.form_filename)
                        attachment = UserAttachment(filename=agent_state.form_filename, content=file_content)
                        result = await extract_form_fields_step.execute(
                            step_context=build_step_context(config.extract_form_fields_config),
                            potential_form_attachment=attachment,
                        )

                        match result:
                            case extract_form_fields_step.CompleteResult():
                                await _send_message(context, result.message, result.debug, MessageType.notice)

                                agent_state.extracted_form = result.extracted_form
                                agent_state.mode = state.FormFillExtensionMode.fill_form_step

                                continue

                            case _:
                                await _handle_incomplete_result(context, result)

                                agent_state.mode = state.FormFillExtensionMode.acquire_form_step
                                return

                    case state.FormFillExtensionMode.fill_form_step:
                        if agent_state.extracted_form is None:
                            raise ValueError("extracted_form is None")

                        result = await fill_form_step.execute(
                            step_context=build_step_context(config.fill_form_config),
                            form_filename=agent_state.form_filename,
                            form=agent_state.extracted_form,
                        )

                        match result:
                            case fill_form_step.CompleteResult():
                                await _send_message(context, result.message, result.debug)

                                agent_state.populated_form_markdown = result.populated_form_markdown
                                agent_state.fill_form_gc_artifact = result.artifact
                                agent_state.mode = state.FormFillExtensionMode.conversation_over

                                continue

                            case _:
                                await _handle_incomplete_result(context, result)
                                return

                    case state.FormFillExtensionMode.conversation_over:
                        await _send_message(
                            context,
                            "The form is now complete! Create a new conversation to work with another form.",
                            {},
                        )
                        return

                    case _:
                        raise ValueError(f"Unexpected mode: {agent_state.mode}")


async def _handle_incomplete_result(context: ConversationContext, result: IncompleteResult) -> None:
    match result:
        case IncompleteResult():
            await _send_message(context, result.message, result.debug)

        case IncompleteErrorResult():
            await _send_error_message(context, result.error_message, result.debug)

        case _:
            raise ValueError(f"Unexpected incomplete result type: {result}")


async def _send_message(
    context: ConversationContext, message: str, debug: dict, message_type: MessageType = MessageType.chat
) -> None:
    if not message:
        return

    await context.send_messages(
        NewConversationMessage(
            content=message,
            message_type=message_type,
            debug_data=debug,
        )
    )


async def _send_error_message(context: ConversationContext, message: str, debug: dict) -> None:
    await context.send_messages(
        NewConversationMessage(
            content=message,
            message_type=MessageType.notice,
            debug_data=debug,
        )
    )
