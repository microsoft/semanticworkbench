from guided_conversation.utils.resources import ResourceConstraintMode, ResourceConstraintUnit
from pydantic import BaseModel, Field

from .config import GuidedConversationConfigModel, ResourceConstraintConfigModel
from .guided_conversation import GC_ConversationStatus, GC_UserDecision


# Artifact - The artifact is like a form that the agent must complete throughout the conversation.
# It can also be thought of as a working memory for the agent.
# We allow any valid Pydantic BaseModel class to be used.
class ArtifactModel(BaseModel):
    final_response: str = Field(
        description="The final response from the agent to the user. You will update this field."
    )
    conversation_status: str = Field(
        description=f"The status of the conversation. May be {GC_ConversationStatus.USER_INITIATED}, {GC_ConversationStatus.USER_RETURNED}, or "
        f"{GC_ConversationStatus.USER_COMPLETED}. You are only allowed to update this field to {GC_ConversationStatus.USER_COMPLETED}, otherwise you will NOT update it.",
    )
    user_decision: str = Field(
        description=f"The decision of the user on what should happen next. May be {GC_UserDecision.UPDATE_OUTLINE}, "
        f"{GC_UserDecision.DRAFT_PAPER}, or {GC_UserDecision.EXIT_EARLY}. You will update this field."
    )
    filenames: str = Field(
        description="Names of the available files currently uploaded as attachments. Information "
        "from the content of these files was used to help draft the outline under review. You "
        "CANNOT change this field."
    )
    current_outline: str = Field(
        description="The most up-to-date version of the outline under review. You CANNOT change this field."
    )


# Rules - These are the do's and don'ts that the agent should follow during the conversation.
rules = [
    "Do NOT rewrite or update the outline, even if the user asks you to.",
    "Do NOT show the outline, unless the user asks you to.",
    (
        "You are ONLY allowed to help the user decide on any changes to the outline or answer questions "
        "about writing an outline."
    ),
    (
        "You are only allowed to update conversation_status to user_completed. All other values for that field"
        " will be preset."
    ),
    (
        "If the conversation_status is marked as user_completed, the final_response and user_decision cannot be left as "
        "Unanswered. The final_response and user_decision must be set based on the conversation flow instructions."
    ),
    "Terminate the conversation immediately if the user asks for harmful or inappropriate content.",
]

# Conversation Flow (optional) - This defines in natural language the steps of the conversation.
conversation_flow = f"""
1. If there is no prior conversation history to reference, use the conversation_status to determine if the user is initiating a new conversation (user_initiated) or returning to an existing conversation (user_returned).
2. Only greet the user if the user is initiating a new conversation. If the user is NOT initiating a new conversation, you should respond as if you are in the middle of a conversation.  In this scenario, do not say "hello", or "welcome back" or any type of formalized greeting.
3. Start by asking the user to review the outline. The outline will have already been provided to the user. You do not provide the outline yourself unless the user
specifically asks for it from you.
4. Answer any questions about the outline or the drafting process the user inquires about.
5. Use the following logic to fill in the artifact fields:
a. At any time, if the user asks for a change to the outline, the conversation_status must be
marked as user_completed. The user_decision must be marked as update_outline. The final_response
must inform the user that a new outline is being generated based off the request.
b. At any time, if the user has provided new attachments (detected via `Newly attached files:` in the user message),
the conversation_status must be marked as {GC_ConversationStatus.USER_COMPLETED}. The user_decision must be marked as
{GC_UserDecision.UPDATE_OUTLINE}. The final_response must inform the user that a new outline is being generated based
on the addition of new attachments.
c. At any time, if the user is good with the outline in its current form and ready to move on to
drafting a paper from it, the conversation_status must be marked as {GC_ConversationStatus.USER_COMPLETED}. The
user_decision must be marked as {GC_UserDecision.DRAFT_PAPER}. The final_response must inform the user that you will
start drafting the beginning of the document based on this outline.
"""

# Context (optional) - This is any additional information or the circumstances the agent is in that it should be aware of.
# It can also include the high level goal of the conversation if needed.
context = """You are working with a user on drafting an outline. The current drafted outline is
provided, along with any filenames that were used to help draft the outline. You do not have access
to the content within the filenames that were used to help draft the outline. Your purpose here is
to help the user decide on any changes to the outline they might want or answer questions about it.
This may be the first time the user is asking for you help (conversation_status is user_initiated),
or the nth time (conversation_status is user_returned)."""

config = GuidedConversationConfigModel(
    rules=rules,
    conversation_flow=conversation_flow.strip(),
    context=context.strip(),
    resource_constraint=ResourceConstraintConfigModel(
        unit=ResourceConstraintUnit.TURNS,
        mode=ResourceConstraintMode.MAXIMUM,
        quantity=5,
    ),
)
