import logging
import re
from contextvars import ContextVar
from dataclasses import dataclass
from textwrap import dedent
from typing import Any, AsyncIterable, Iterable, Literal

import openai_client
from openai.types.chat import (
    ChatCompletionMessageParam,
    ChatCompletionMessageToolCallParam,
)
from pydantic import BaseModel, Field
from semantic_workbench_api_model.workbench_model import (
    ConversationEvent,
    ConversationMessage,
    MessageType,
    NewConversationMessage,
    ParticipantRole,
)
from semantic_workbench_assistant.assistant_app.config import BaseModelAssistantConfig
from semantic_workbench_assistant.assistant_app.context import ConversationContext
from semantic_workbench_assistant.assistant_app.protocol import AssistantAppProtocol

from ..config import AssistantConfigModel
from . import store, tools
from ._llm import CompletionTool, MessageResponse, ToolCallResponse, completion_with_tools
from .config import LLMConfig

logger = logging.getLogger(__name__)


system_message_document_assistant = dedent("""
    You are an assistant. Ultimately, you help users create documents in a document workspace. To do this, you
    will assist with ideation, drafting, and editing. Documents are can represent a variety of content types,
    such as reports, articles, blog posts, stories, slide decks or others. You can create, update, and remove
    documents, as well as create, update, and remove sections within documents.
    When updating the content of sections, by calling create_document_section or update_document_section,
    you will always ensure that the purpose, audience and other_guidelines of the document and respective
    section are adhered to, if they are set.
""")

# document_workspace_inspector = store.DocumentWorkspaceInspector()
active_document_inspector = store.AllDocumentsInspector()


@dataclass
class LLMs:
    fast: LLMConfig
    chat: LLMConfig
    reasoning_fast: LLMConfig
    reasoning_long: LLMConfig


class ArtifactCreationExtension:
    def __init__(
        self, assistant_app: AssistantAppProtocol, assistant_config: BaseModelAssistantConfig[AssistantConfigModel]
    ) -> None:
        # assistant_app.add_inspector_state_provider(
        #     document_workspace_inspector.display_name, document_workspace_inspector
        # )
        assistant_app.add_inspector_state_provider(active_document_inspector.display_name, active_document_inspector)

        @assistant_app.events.conversation.message.command.on_created
        async def on_message_command_created(
            context: ConversationContext, _: ConversationEvent, message: ConversationMessage
        ) -> None:
            config = await assistant_config.get(context.assistant)
            if config.guided_workflow != "Long Document Creation":
                return

            match message.content.split(" ")[0]:
                case "/help":
                    await _send_message(
                        dedent("""
                        /help - Display this help message.
                        /ls - List all documents in the workspace.
                        /select <number> - Select the active document."""),
                        {},
                        message_type=MessageType.command_response,
                        generated_content=False,
                    )

                case "/ls":
                    args = tools.ListDocumentsArgs()
                    headers = await tools.list_documents(args)
                    document_list = "\n".join(
                        f"{index}. {header.title} ({header.document_id})"
                        for index, header in enumerate(headers.documents)
                    )
                    await _send_message(
                        f"Documents in the workspace: {headers.count}\n\n{document_list}",
                        {},
                        message_type=MessageType.command_response,
                        generated_content=False,
                    )

                case _:
                    await _send_message(
                        "Unknown command. Use /help to see available commands.",
                        {},
                        message_type=MessageType.command_response,
                        generated_content=False,
                    )

        @assistant_app.events.conversation.message.chat.on_created
        async def on_message_chat_created(
            context: ConversationContext, _: ConversationEvent, message: ConversationMessage
        ) -> None:
            config = await assistant_config.get(context.assistant)
            if config.guided_workflow != "Long Document Creation":
                return

            tools.current_document_store.set(store.for_context(context))
            current_context.set(context)

            chat_model = "gpt-4o"
            fast_model = "gpt-4o-mini"
            reasoning_model = "o3-mini"
            chat_service_config = config.service_config.model_copy(deep=True)
            chat_service_config.azure_openai_deployment = chat_model  # type: ignore
            fast_service_config = config.service_config.model_copy(deep=True)
            fast_service_config.azure_openai_deployment = fast_model  # type: ignore
            reasoning_fast_service_config = config.service_config.model_copy(deep=True)
            reasoning_fast_service_config.azure_openai_deployment = reasoning_model  # type: ignore
            reasoning_long_service_config = config.service_config.model_copy(deep=True)
            reasoning_long_service_config.azure_openai_deployment = reasoning_model  # type: ignore

            llms = LLMs(
                fast=LLMConfig(
                    openai_client_factory=lambda: openai_client.create_client(fast_service_config),
                    openai_model=fast_model,
                    max_response_tokens=config.request_config.response_tokens,
                ),
                chat=LLMConfig(
                    openai_client_factory=lambda: openai_client.create_client(chat_service_config),
                    openai_model=chat_model,
                    max_response_tokens=config.request_config.response_tokens,
                ),
                reasoning_fast=LLMConfig(
                    openai_client_factory=lambda: openai_client.create_client(reasoning_fast_service_config),
                    openai_model=reasoning_model,
                    max_response_tokens=config.request_config.response_tokens,
                    reasoning_effort="low",
                ),
                reasoning_long=LLMConfig(
                    openai_client_factory=lambda: openai_client.create_client(reasoning_long_service_config),
                    openai_model=reasoning_model,
                    max_response_tokens=90_000,
                    reasoning_effort="high",
                ),
            )

            messages_response = await context.get_messages(before=message.id)
            chat_history = (*(message for message in messages_response.messages), message)

            async with context.set_status("responding ..."):
                await respond_to_message(llms=llms, conversation_history=chat_history)


completion_tools: list[CompletionTool] = [
    CompletionTool(
        function=tools.create_document,
        argument_model=tools.CreateDocumentArgs,
    ),
    CompletionTool(
        function=tools.update_document,
        argument_model=tools.UpdateDocumentArgs,
    ),
    CompletionTool(
        function=tools.remove_document,
        argument_model=tools.RemoveDocumentArgs,
    ),
    CompletionTool(
        function=tools.create_document_section,
        argument_model=tools.CreateDocumentSectionArgs,
    ),
    CompletionTool(
        function=tools.update_document_section,
        argument_model=tools.UpdateDocumentSectionArgs,
    ),
    CompletionTool(
        function=tools.remove_document_section,
        argument_model=tools.RemoveDocumentSectionArgs,
    ),
    # CompletionTool(
    #     function=tools.get_document,
    #     argument_model=tools.GetDocumentArgs,
    # ),
    # CompletionTool(
    #     function=tools.list_documents,
    #     argument_model=tools.ListDocumentsArgs,
    # ),
]

tool_list_for_plan = "\n".join(
    f"- Function: {tool.function.__name__}; Args: {tool.argument_model.model_json_schema()}"
    for tool in completion_tools
)

system_message_plan_for_turn = dedent(f"""
    You are responsible for recommending the next action to take in the conversation.
    This action will be executed by another assistant.

    # RECOMMENDED NEXT ACTION
    You will recommend either clarifying the document change request, making the requested document changes,
    or continuing the conversation.

    ## continue_conversation
    Continuing the conversation means that you have determined that the user is not requesting changes to
    the document, and the conversation should be continued. For example, the user may be asking a question
    about the document, asking a question general knowledge, chatting, or providing additional information.

    ## clarify_document_change_request
    Clarifying the document change request means that you have determined that the user is requesting changes,
    however the request could use clarification. Or it is possible that the user message coulud be interpreted
    as a request to make changes, but it is not clear. You will set 'clarification_question' to instruct
    the assistant on what clarifications to make with the user.

    ## make_document_changes
    Making the requested document changes means that you have determined that the user is requesting changes to
    the document, or documents, and there is clarity on what changes are needed.
    When considering what changes to make, make sure you review the content of the document and all sections
    within the document to determine if they need to be changed.
    You will set 'document_changes_explanation' to explain the changes and 'document_changes_tool_calls' to list
    the tool calls that you recommend to make the requested changes.

    Document changes explanation must:
    - Explain the changes that are needed in the document and how they should be implemented.
    - Speak in the first person, as if you are the assistant that will execute the plan. For example, do not use
      "We will", "We are going to" or "The assistant will".

    When recommending an action of make_document_changes, and recommending calls to `create_document_section` or
    `update_document_section, you must:
    - specify the `content` argument as "<content>", the content placeholder, to indicate that the content should
      be generated by the assistant that will execute the plan.
    - specify the `document_id` argument as the id for the appropriate document, if it exists at the time this plan
      is being created.
    - specify the `document_id` as "<document_id>", the document id placeholder, if the document is being created
      in this plan. The placeholder will be replaced with the result of the `create_document` tool call when the
      plan is executed.

    Tool call explanations, for the assistant that will execute the plan, must:
    - Explain the intent of the tool call.
    - Ensure the explanation is thorough and clear.
    - The explanation is for an LLM that will execute the plan - the explanation is not for the user.

    Content placeholder replacement instructions, for the assistant that will execute the plan, must:
    - Explain in specific detail what content to generate.
    - Include relevant considerations based on the document purpose.
    - Include relevant considerations based on the document other_guidelines.
    - Include relevant considerations based on the section purpose.
    - Include all context, as the assistant that will execute the plan will not have access to the user's request.

    Example of a BAD content placeholder replacement instruction:
    "Replace the <content> placeholder with content."

    Example of a GOOD explanation: (for a document with purpose "to summarize findings from another document" and other_guidelines "use bullet points")
    "Replace the <content> placeholder with a detailed summary of the document, including the main points in a bulleted list."

    # TOOLS AVAILABLE FOR DOCUMENT CHANGES

    {tool_list_for_plan}
""")


system_message_clarify_document_change_request = dedent("""
    It seems likely that the user is requesting changes to the document.
    A question has been posed by another AI assistant to clarify the request.

    Ask the user, in you own words, the question posed by the other AI assistant.

    # QUESTION TO ASK THE USER
    {clarification_question}
""")

system_message_make_document_changes = dedent("""
    The user is requesting changes to the document.
    A multi-step plan has been created to implement the changes.
    You will execute a single step in the plan, by calling the recommended tool.

    If you decide to share a text message in addition to the tool call, do not refer
    to the plan, but rather explain the changes in your own words, and in the context
    of what the user requested in their last message.

    # EXPLANATION OF THE FULL PLAN

    NOTE: This full plan is provided for context. You do not need to execute on it. You will execute
    only the current step.

    {plan_explanation}

    # CURRENT STEP TO EXECUTE

    NOTE: This is the step you will execute.
    NOTE: The "<content>" placeholder in the recommended tool call must be replaced with generated
          content based on the content placeholder replacement instructions.

    {step_plan}
""")

system_message_make_document_changes_complete = dedent("""
    Congratulations!

    You have just now completed the changes requested by the user according to a plan.
    The document in the workspace reflects the changes you've made.

    Your job now is to explain what you've done to complete the user's request.
    Explain in your own words and taking into consideration the plan below and the
    user's request in their last message.

    - Do NOT refer to the plan.
    - Explain the changes as though you just did them
    - Do NOT explain them as though they are already done.

    For example:
    - say "I have created a new document ..." instead of "The document already existed ..."
    - say "I have added a new section ..." instead of "The section already existed ..."
    - say "I have updated the document ..." instead of "The document was already updated ..."

    # THE PLAN YOU JUST COMPLETED

    {plan_explanation}
""")


class ToolCall(BaseModel):
    call: str = Field(
        description="The recommended tool call to make. Example format: function_name({arg1: value1, arg2: value2})"
    )
    explanation: str = Field(
        description="An explanation of why this tool call is being made and what it is trying to accomplish."
    )
    content_instructions: str = Field(
        description="Specific instructions on how to replace the <content> placeholder in the tool call with generated content."
    )


class PlanForTurn(BaseModel):
    recommended_next_action: Literal[
        "clarify_document_change_request", "make_document_changes", "continue_conversation"
    ] = Field(
        description=dedent("""
        The recommended next action to take.
        If 'clarify_document_change_request', you have determined that the user is requesting changes to the document, however
        the request could use clarification; additionally, you will set 'clarification_question' to prompt the user for more
        information.
        If 'make_document_changes', you have determined that the user is requesting changes to the document and there is
        clarity on what changes are needed; additionally, you will set 'document_changes_explanation' to explain the changes
        and 'document_changes_tool_calls' to list the tool calls that you recommend to make the changes.
        If 'continue_conversation', you have determined that the user is not requesting changes to the document and the conversation
        should be continued.
        """)
    )
    clarification_question: str | None = Field(
        description=dedent("""
        A question to prompt the user for more information about the document change request - should be set only if
        'recommended_next_action' is 'clarify_document_change_request'.
        """)
    )
    document_changes_explanation: str | None = Field(
        description=dedent("""
        An explanation of the changes that are needed in the document - should be set only if 'recommended_next_action
        is 'make_document_changes'.
        """)
    )
    document_changes_tool_calls: list[ToolCall] | None = Field(
        description=dedent("""
        A list of tool calls that you recommend to make the changes in the document - should be set only if
        'recommended_next_action' is 'make_document_changes'.
        """)
    )


async def system_message_generator(message: str) -> list[ChatCompletionMessageParam]:
    return [
        openai_client.create_developer_message(content=message),
    ]


async def chat_message_generator(history: Iterable[ConversationMessage]) -> list[ChatCompletionMessageParam]:
    messages: list[ChatCompletionMessageParam] = []
    for msg in history:
        match msg.sender.participant_role:
            case ParticipantRole.user:
                messages.append(openai_client.create_user_message(content=msg.content))

            case ParticipantRole.assistant:
                messages.append(openai_client.create_assistant_message(content=msg.content))

    headers = await tools.list_documents(tools.ListDocumentsArgs())
    document_content_list: list[str] = []
    document_content_list.append(f"There are currently {len(headers.documents)} documents in the workspace.")

    for header in headers.documents:
        document = await tools.get_document(tools.GetDocumentArgs(document_id=header.document_id))
        document_content_list.append(f"```json\n{document.model_dump_json()}\n```")

    document_content = "\n\n".join(document_content_list)

    last_assistant_index = 0
    for i in range(1, len(messages)):
        if messages[-i].get("role") == "assistant":
            last_assistant_index = len(messages) - i
            break

    if last_assistant_index >= 0:
        messages = (
            messages[:last_assistant_index]
            + [
                openai_client.create_assistant_message(
                    content=None,
                    tool_calls=[
                        ChatCompletionMessageToolCallParam(
                            id="call_1",
                            function={
                                "name": "get_all_documents",
                                "arguments": "{}",
                            },
                            type="function",
                        )
                    ],
                ),
                openai_client.create_tool_message(
                    tool_call_id="call_1",
                    content=document_content,
                ),
            ]
            + messages[last_assistant_index:]
        )

    return messages


async def respond_to_message(
    llms: LLMs,
    conversation_history: Iterable[ConversationMessage],
) -> None:
    async with current_context.get().set_status("planning..."):
        try:
            plan_for_turn = await build_plan_for_turn(llms=llms, history=conversation_history)
        except Exception as e:
            logger.exception("Failed to generate plan.")
            await _send_error_message("Failed to generate plan.", {"error": str(e)})
            return

    try:
        await execute_plan(llms=llms, history=conversation_history, plan_for_turn=plan_for_turn)
    except Exception as e:
        logger.exception("Failed to generate completion.")
        await _send_error_message("Failed to generate completion.", {"error": str(e)})
        return


async def build_plan_for_turn(llms: LLMs, history: Iterable[ConversationMessage]) -> PlanForTurn:
    async with llms.reasoning_fast.openai_client_factory() as client:
        logger.info("generating plan")
        structured_response = await openai_client.completion_structured(
            async_client=client,
            messages=await chat_message_generator(history)
            + await system_message_generator(system_message_plan_for_turn),
            response_model=PlanForTurn,
            openai_model=llms.reasoning_fast.openai_model,
            max_completion_tokens=llms.reasoning_fast.max_response_tokens,
            reasoning_effort=llms.reasoning_fast.reasoning_effort,
        )
        plan_for_turn = structured_response.response
        metadata = structured_response.metadata
        logger.info("plan_for_turn: %s", plan_for_turn)

    await _send_message(
        (
            f"Recommended next action: {plan_for_turn.recommended_next_action}; "
            f"{plan_for_turn.document_changes_explanation or plan_for_turn.clarification_question or ''}"
        ),
        {
            **metadata,
            "plan_for_turn": plan_for_turn.model_dump(mode="json"),
        },
        message_type=MessageType.notice,
    )

    return plan_for_turn


async def execute_plan(llms: LLMs, history: Iterable[ConversationMessage], plan_for_turn: PlanForTurn) -> None:
    async def generate_steps_from_plan() -> AsyncIterable[tuple[str, str, int, bool, list[CompletionTool]]]:
        match plan_for_turn.recommended_next_action:
            case "continue_conversation":
                yield "", "", -1, True, []

            case "clarify_document_change_request":
                step_plan = system_message_clarify_document_change_request.replace(
                    "{clarification_question}", plan_for_turn.clarification_question or ""
                )
                yield step_plan, "", -1, True, []

            case "make_document_changes":
                for recommendation in plan_for_turn.document_changes_tool_calls or []:
                    document_id = "<document_id>"
                    headers = await tools.list_documents(tools.ListDocumentsArgs())
                    if headers.documents:
                        document_id = headers.documents[0].document_id

                    call_with_document_id = re.sub(r"<document_id>", document_id, recommendation.call, 1, re.IGNORECASE)
                    tool_plan = "\n\n".join([
                        f"Explanation for tool call:\n{recommendation.explanation}",
                        f"Content placeholder replacement instructions:\n{recommendation.content_instructions}",
                        f"Call:\n{call_with_document_id}",
                    ])
                    step_plan = system_message_make_document_changes.replace(
                        "{plan_explanation}", plan_for_turn.document_changes_explanation or ""
                    ).replace("{step_plan}", tool_plan)
                    tool_choice = recommendation.call.split("(")[0]
                    step_tools = [tool for tool in completion_tools if tool.function.__name__ == tool_choice]
                    yield (step_plan, recommendation.call.split("(")[0], 0, False, step_tools)

                yield (
                    system_message_make_document_changes_complete.replace(
                        "{plan_explanation}", plan_for_turn.document_changes_explanation or ""
                    ),
                    "",
                    -1,
                    True,
                    [],
                )

            case _:
                raise ValueError(f"Unsupported recommended_next_action: {plan_for_turn.recommended_next_action}")

    additional_messages: list[ConversationMessage] = []

    async for (
        step_plan,
        tool_choice,
        ignore_tool_calls_after,
        allow_tool_followup,
        plan_tools,
    ) in generate_steps_from_plan():
        logger.info("executing step plan: %s", step_plan)
        async for response in completion_with_tools(
            llm_config=llms.chat,
            head_messages=lambda: chat_message_generator((*history, *additional_messages)),
            tail_messages=lambda: system_message_generator(system_message_document_assistant + step_plan),
            tools=plan_tools,
            tool_choice={"function": {"name": tool_choice}, "type": "function"} if tool_choice else None,
            ignore_tool_calls_after=ignore_tool_calls_after,
            allow_tool_followup=allow_tool_followup,
        ):
            match response:
                case MessageResponse():
                    message = await _send_message(response.message, debug=response.metadata)
                    if message is not None:
                        additional_messages.append(message)

                case ToolCallResponse():
                    # async with (
                    #     current_context.get().state_updated_event_after(document_workspace_inspector.display_name),
                    #     current_context.get().state_updated_event_after(active_document_inspector.display_name),
                    # ):
                    async with current_context.get().state_updated_event_after(active_document_inspector.display_name):
                        await _send_message(
                            response.result,
                            response.metadata,
                            message_type=MessageType.notice,
                            generated_content=False,
                        )


async def _send_message(
    message: str,
    debug: dict[str, Any],
    message_type: MessageType = MessageType.chat,
    metadata: dict[str, Any] | None = None,
    generated_content: bool = True,
) -> ConversationMessage | None:
    if not message:
        return None

    if not generated_content:
        metadata = {"generated_content": False, **(metadata or {})}

    footer_items = _footer_items_for(debug)
    if footer_items:
        metadata = {"footer_items": footer_items, **(metadata or {})}

    message_list = await current_context.get().send_messages(
        NewConversationMessage(
            content=message,
            message_type=message_type,
            metadata=metadata,
            debug_data=debug,
        )
    )

    return message_list.messages[0] if message_list.messages else None


def _footer_items_for(debug: dict[str, Any]) -> list[str]:
    footer_items = []

    def format_duration(duration: float) -> str:
        if duration < 1:
            return f"{duration * 1_000:.0f} milliseconds"
        if duration < 60:
            return f"{duration:.2f} seconds"
        if duration < 3600:
            return f"{duration / 60:.2f} minutes"
        return f"{duration / 3600:.2f} hours"

    if "response_duration" in debug:
        footer_items.append(f"Response time: {format_duration(debug['response_duration'])}")

    if "tool_duration" in debug:
        footer_items.append(f"Tool time: {format_duration(debug['tool_duration'])}")

    def format_tokens(tokens: int) -> str:
        if tokens < 1_000:
            return f"{tokens:,}"
        if tokens < 1_000_000:
            return f"{tokens / 1_000:.1f}K"
        return f"{tokens / 1_000_000:.1f}M"

    if "response" in debug:
        if "usage" in debug["response"]:
            usage = debug["response"]["usage"]
            footer_items.append(
                f"Tokens: {format_tokens(usage['total_tokens'])} ({format_tokens(usage['prompt_tokens'])} in, {format_tokens(usage['completion_tokens'])} out)"
            )

        if "model" in debug["response"]:
            footer_items.append(f"Model: {debug['response']['model']}")

    return footer_items


async def _send_error_message(message: str, debug: dict[str, Any]) -> None:
    await _send_message(
        message=message,
        debug=debug,
        message_type=MessageType.notice,
        generated_content=False,
    )


current_context: ContextVar[ConversationContext] = ContextVar("current_conversation_context")
