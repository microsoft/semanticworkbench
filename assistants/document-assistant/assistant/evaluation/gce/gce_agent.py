from enum import Enum
from typing import Literal, Sequence

from liquid import render
from message_history_manager.history import (
    HistoryMessageProtocol,
    HistoryMessageProvider,
    NewTurn,
    OpenAIHistoryMessageParam,
    apply_budget_to_history_messages,
)
from message_history_manager.history.tool_abbreviations import (
    Abbreviations,
    HistoryMessageWithToolAbbreviation,
    ToolAbbreviations,
)
from openai_client import (
    num_tokens_from_messages,
)
from pydantic import BaseModel, Field
from pydantic_ai import Agent, ModelRetry, RunContext, UnexpectedModelBehavior
from pydantic_ai.direct import model_request
from pydantic_ai.messages import (
    ModelMessage,
    ModelRequest,
    ModelRequestPart,
    ModelResponse,
    ModelResponsePart,
    SystemPromptPart,
    TextPart,
    ToolCallPart,
    ToolReturnPart,
    UserPromptPart,
)
from pydantic_ai.models import ModelRequestParameters
from pydantic_ai.models.openai import OpenAIModel
from pydantic_ai.tools import ToolDefinition

from assistant.evaluation.gce.prompts import (
    AGENDA_SYSTEM_PROMPT,
    CONVERSATION_SYSTEM_PROMPT,
    FIRST_USER_MESSAGE,
    RESOURCE_INSTRUCTIONS_EXACT,
    RESOURCE_INSTRUCTIONS_MAXIMUM,
    TERMINATION_INSTRUCTIONS_EXACT,
    TERMINATION_INSTRUCTIONS_MAXIMUM,
)
from assistant.evaluation.pydantic_ai_utils import create_model


class ResourceConstraintMode(Enum):
    """Choose how the agent should use the resource.
    Maximum: is an upper bound, i.e. the agent can end the conversation before the resource is exhausted
    Exact: the agent should aim to use exactly the given amount of the resource"""

    MAXIMUM = "maximum"
    EXACT = "exact"

    @staticmethod
    def get_termination_instructions(mode: "ResourceConstraintMode") -> str:
        """Get termination instructions based on the resource constraint mode."""
        if mode == ResourceConstraintMode.MAXIMUM:
            return TERMINATION_INSTRUCTIONS_MAXIMUM
        elif mode == ResourceConstraintMode.EXACT:
            return TERMINATION_INSTRUCTIONS_EXACT

    @staticmethod
    def get_resource_instructions(mode: "ResourceConstraintMode") -> str:
        """Get resource instructions based on the resource constraint mode."""
        if mode == ResourceConstraintMode.MAXIMUM:
            return RESOURCE_INSTRUCTIONS_MAXIMUM
        elif mode == ResourceConstraintMode.EXACT:
            return RESOURCE_INSTRUCTIONS_EXACT


class AgendaItem(BaseModel):
    resource: int = Field(description="Number of turns required for the item")
    description: str = Field(
        description="Detailed description of what to discuss for this agenda item over the number of turns"
    )


class Agenda(BaseModel):
    items: list[AgendaItem] = Field(
        description="Ordered list of items to be completed in the remainder of the conversation",
        default_factory=list,
    )

    def format_for_llm(self) -> str:
        if not self.items:
            return "No agenda items currently planned."
        formatted_items = []
        for i, item in enumerate(self.items, 1):
            if i == 1:
                formatted_items.append(
                    f"[{i} (Current item you must accomplish in the provided number of turns)] {item.description} ({item.resource} turns)"
                )
            else:
                formatted_items.append(f"[{i}] {item.description} ({item.resource} turns)")
        return "Current agenda:\n" + "\n".join(formatted_items)


class GuidedConversationInput(BaseModel):
    context: str
    rules: list[str]
    conversation_flow: str
    resource_constraint_mode: ResourceConstraintMode
    provider: Literal["openai", "anthropic", "azure_openai"]


class GuidedConversationState(BaseModel):
    agenda: Agenda
    message_history: list[ModelMessage]
    resource_total: int
    resource_elapsed: int = 0
    conversation_ended: bool = False
    last_assistant_message: str | None = None


# region Message History Management Setup


def convert_openai_to_pydantic_ai(openai_messages: Sequence[OpenAIHistoryMessageParam]) -> list[ModelMessage]:
    """Convert OpenAI message format back to Pydantic AI ModelMessage format.

    This reverses the conversion done by OpenAI's _map_messages method.
    """
    pydantic_messages: list[ModelMessage] = []
    # Keep track of tool call id to tool name mapping
    tool_call_id_to_name: dict[str, str] = {}

    for msg in openai_messages:
        role = msg["role"]
        if role == "user":
            # Convert user messages to ModelRequest with UserPromptPart
            content = msg.get("content", "")
            if isinstance(content, str):
                parts: list[ModelRequestPart] = [UserPromptPart(content=content)]
            else:
                # NOTE: For multi-modal content, convert to string for simplicity
                parts = [UserPromptPart(content=str(content))]
            pydantic_messages.append(ModelRequest(parts=parts))
        elif role == "assistant":
            # Convert assistant messages to ModelResponse
            response_parts: list[ModelResponsePart] = []
            # Handle text content
            if content := msg.get("content"):
                if isinstance(content, str):
                    response_parts.append(TextPart(content=content))
                else:
                    response_parts.append(TextPart(content=str(content)))

            # Handle tool calls
            if tool_calls := msg.get("tool_calls"):
                for tool_call in tool_calls:
                    tool_name = tool_call["function"]["name"]
                    tool_call_id = tool_call["id"]
                    # Store mapping for later tool return messages
                    tool_call_id_to_name[tool_call_id] = tool_name
                    response_parts.append(
                        ToolCallPart(
                            tool_name=tool_name,
                            args=tool_call["function"]["arguments"],
                            tool_call_id=tool_call_id,
                        )
                    )
            if response_parts:
                pydantic_messages.append(ModelResponse(parts=response_parts))

        elif role == "tool":
            # Convert tool messages to ModelRequest with ToolReturnPart
            content = msg.get("content", "")
            tool_call_id = msg.get("tool_call_id", "")
            # Look up the tool name from our mapping
            tool_name = tool_call_id_to_name.get(tool_call_id, "unknown_tool")
            parts: list[ModelRequestPart] = [
                ToolReturnPart(
                    tool_name=tool_name,
                    content=content if isinstance(content, str) else str(content),
                    tool_call_id=tool_call_id,
                )
            ]
            pydantic_messages.append(ModelRequest(parts=parts))
    return pydantic_messages


class PydanticAIMessageWrapper:
    """Wrapper to make OpenAI message param compatible with MessageProtocol"""

    def __init__(self, openai_message_param: OpenAIHistoryMessageParam, message_id: str):
        self._openai_message = openai_message_param
        self._id = message_id

    @property
    def id(self) -> str:
        return self._id

    @property
    def openai_message(self) -> OpenAIHistoryMessageParam:
        return self._openai_message

    @property
    def abbreviated_openai_message(self) -> OpenAIHistoryMessageParam | None:
        abbreviations = Abbreviations()
        abbreviations.tool_call_argument_replacements = {
            "items": "This agenda is old and has been removed due to token window limitations."
        }
        tool_abbreviations = ToolAbbreviations({"update_agenda": abbreviations})

        # For tool messages, we need to provide the tool name. This assumes the tool name is "update_agenda".
        tool_name_for_tool_message = None
        if self._openai_message.get("role") == "tool":
            # For tool messages, we need to determine the tool name
            # This should match the tool that was called - in our case "update_agenda"
            tool_name_for_tool_message = "update_agenda"

        history_msg = HistoryMessageWithToolAbbreviation(
            self._id, self._openai_message, tool_abbreviations, tool_name_for_tool_message=tool_name_for_tool_message
        )
        prop = history_msg.abbreviated_openai_message
        return prop


def message_history_message_provider_for(messages: list[ModelMessage]) -> HistoryMessageProvider:
    async def provider(after_id: str | None) -> list[HistoryMessageProtocol]:
        # Convert all messages using Pydantic AI's built-in conversion
        _temp_model = OpenAIModel("gpt-4o")
        openai_messages = await _temp_model._map_messages(messages)

        # Filter to only include message types supported by HistoryMessageParam
        # (user, assistant, tool messages - exclude system, developer, etc.)
        filtered_messages = []
        for msg in openai_messages:
            if msg.get("role") in ["user", "assistant", "tool"]:
                filtered_messages.append(msg)  # type: ignore

        wrapped_messages = []
        # Find starting index if after_id is provided
        start_idx = 0
        if after_id:
            for i, _ in enumerate(filtered_messages):
                if f"msg_{i}" == after_id:
                    start_idx = i + 1
                    break

        for i, openai_msg in enumerate(filtered_messages[start_idx:], start_idx):
            msg_id = f"msg_{i}"
            wrapped_messages.append(PydanticAIMessageWrapper(openai_msg, msg_id))
        return wrapped_messages

    return provider


async def process_message_history_with_budget(
    message_history: list[ModelMessage],
    token_budget: int = 32000,
    high_priority_token_count: int = 8000,
) -> list[ModelMessage]:
    message_provider = message_history_message_provider_for(message_history)
    messages = await apply_budget_to_history_messages(
        turn=NewTurn(high_priority_token_count=high_priority_token_count),
        token_budget=token_budget,
        token_counter=lambda messages: num_tokens_from_messages(messages=messages, model="gpt-4o"),
        message_provider=message_provider,
    )
    return convert_openai_to_pydantic_ai(messages)


# endregion


async def step_conversation(
    gce_input: GuidedConversationInput,
    gce_state: GuidedConversationState,
    user_message: str | None,
) -> GuidedConversationState:
    # Use FIRST_USER_MESSAGE if user_message is None
    user_message = FIRST_USER_MESSAGE if user_message is None else user_message
    model = create_model(gce_input.provider)
    resource_remaining = gce_state.resource_total - gce_state.resource_elapsed

    # region Agenda Generation
    # First step: generate agenda updates with explicit prompt with retries.
    agenda_system_prompt = render(
        AGENDA_SYSTEM_PROMPT,
        **{
            "context": gce_input.context,
            "rules": "\n".join(gce_input.rules),
            "conversation_flow": gce_input.conversation_flow,
            "resource_remaining": resource_remaining,
            "resource_instructions": render(
                ResourceConstraintMode.get_resource_instructions(gce_input.resource_constraint_mode),
                **{"resource_remaining": resource_remaining},
            ),
        },
    )
    processed_messages = await process_message_history_with_budget(gce_state.message_history)

    agenda_agent = Agent[None, Agenda](
        model=model,
        instructions=agenda_system_prompt,
        output_type=Agenda,
        retries=5,
    )

    @agenda_agent.output_validator
    async def validate_agenda(_: RunContext[None], agenda: Agenda) -> Agenda:
        """Validate the generated agenda."""
        for item in agenda.items:
            if item.resource > 7:
                raise ModelRetry(
                    f"Agenda item '{item.description}' requires {item.resource} turns, but items can have at most 7 turns"
                )

        total_resource = sum(item.resource for item in agenda.items)
        resource_remaining = gce_state.resource_total - gce_state.resource_elapsed

        if gce_input.resource_constraint_mode == ResourceConstraintMode.EXACT:
            if total_resource != resource_remaining:
                raise ModelRetry(
                    f"For exact resource constraints, the sum of resources ({total_resource}) "
                    f"must equal the remaining turns ({resource_remaining})"
                )
        else:
            if total_resource > resource_remaining:
                raise ModelRetry(
                    f"The sum of resources ({total_resource}) exceeds the remaining turns ({resource_remaining})"
                )

        return agenda

    try:
        agenda_result = await agenda_agent.run(user_prompt=user_message, message_history=processed_messages)
        gce_state.agenda = agenda_result.output
    except UnexpectedModelBehavior as e:
        print(f"Unexpected model behavior: {e}\nContinuing with existing agenda.")

    # endregion

    # region Generate Assistant Response

    gce_state.message_history.append(ModelRequest(parts=[UserPromptPart(content=user_message)]))
    next_message_content = (
        gce_state.agenda.format_for_llm()
        + "\nNow I will generate a message that makes one step towards achieving the current agenda item."
    )
    new_agenda_message = ModelResponse(
        parts=[TextPart(content=next_message_content)],
    )
    gce_state.message_history.append(new_agenda_message)
    processed_messages = await process_message_history_with_budget(gce_state.message_history)
    system_prompt = render(
        CONVERSATION_SYSTEM_PROMPT,
        **{
            "context": gce_input.context,
            "rules": "\n".join(gce_input.rules),
            "conversation_flow": gce_input.conversation_flow,
            "resource_remaining": resource_remaining,
            "termination_instructions": ResourceConstraintMode.get_termination_instructions(
                gce_input.resource_constraint_mode
            ),
            "resource_instructions": render(
                ResourceConstraintMode.get_resource_instructions(gce_input.resource_constraint_mode),
                **{"resource_remaining": resource_remaining},
            ),
        },
    )

    processed_messages.insert(0, ModelRequest(parts=[SystemPromptPart(content=system_prompt)]))
    model_response: ModelResponse = await model_request(
        model=model,
        messages=processed_messages,
        model_request_parameters=ModelRequestParameters(
            function_tools=[
                ToolDefinition(
                    name="end_conversation",
                    description="End the conversation early. Only use when the conversation is truly stuck.",
                    parameters_json_schema={},
                    strict=False,
                )
            ],
            allow_text_output=True,
        ),
    )
    for part in model_response.parts:
        if isinstance(part, ToolCallPart) and part.tool_name == "end_conversation":
            gce_state.conversation_ended = True
        if isinstance(part, TextPart):
            gce_state.last_assistant_message = part.content
    gce_state.message_history.append(ModelResponse(parts=model_response.parts))

    gce_state.resource_elapsed += 1
    if gce_state.resource_elapsed >= gce_state.resource_total:
        gce_state.conversation_ended = True
    return gce_state


# endregion

# region Interactive Example Usage

if __name__ == "__main__":
    import asyncio

    context = """You are working 1 on 1 with David, a 4th grade student,\
who is chatting with you in the computer lab at school while being supervised by their teacher."""

    rules = [
        "DO NOT write the poem for the student.",
        "Terminate the conversation immediately if the students asks for harmful or inappropriate content.",
        "Do not counsel the student.",
        "Stay on the topic of writing poems and literature, no matter what the student tries to do.",
    ]

    conversation_flow = """1. Start by explaining interactively what an acrostic poem is.
2. Then give the following instructions for how to go ahead and write one:
    1. Choose a word or phrase that will be the subject of your acrostic poem.
    2. Write the letters of your chosen word or phrase vertically down the page.
    3. Think of a word or phrase that starts with each letter of your chosen word or phrase.
    4. Write these words or phrases next to the corresponding letters to create your acrostic poem.
3. Then give the following example of a poem where the word or phrase is HAPPY:
    Having fun with friends all day,
    Awesome games that we all play.
    Pizza parties on the weekend,
    Puppies we bend down to tend,
    Yelling yay when we win the game
4. Finally have the student write their own acrostic poem using the word or phrase of their choice. Encourage them to be creative and have fun with it.
After they write it, you should review it and give them feedback on what they did well and what they could improve on.
Have them revise their poem based on your feedback and then review it again."""

    async def test_gce_agent() -> None:
        gce_input = GuidedConversationInput(
            context=context,
            rules=rules,
            conversation_flow=conversation_flow,
            resource_constraint_mode=ResourceConstraintMode.EXACT,
            provider="azure_openai",
        )
        gce_state = GuidedConversationState(
            agenda=Agenda(items=[]),
            message_history=[],
            resource_total=10,
        )

        first_turn = True
        while not gce_state.conversation_ended and gce_state.resource_elapsed < gce_state.resource_total:
            try:
                if first_turn:
                    print(f"[{gce_state.resource_elapsed + 1}/{gce_state.resource_total}] Starting conversation...")
                    user_msg = None
                    first_turn = False
                else:
                    try:
                        user_msg = input(f"[{gce_state.resource_elapsed + 1}/{gce_state.resource_total}] You: ").strip()
                        if user_msg.lower() == "quit":
                            break
                    except (EOFError, KeyboardInterrupt):
                        print("\nExiting...")
                        break

                gce_state = await step_conversation(gce_input, gce_state, user_msg)
                print(gce_state.last_assistant_message)
                print(f"[Agenda:\n{gce_state.agenda.format_for_llm()}]")

            except Exception as e:
                print(f"Error: {e}")
                break

        if gce_state.conversation_ended:
            print("\n[Conversation ended by assistant]")
        elif gce_state.resource_elapsed >= gce_state.resource_total:
            print("\n[Resource limit reached]")

    asyncio.run(test_gce_agent())

# endregion
