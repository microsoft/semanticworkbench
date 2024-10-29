from guided_conversation.utils.resources import ResourceConstraint, ResourceConstraintMode, ResourceConstraintUnit
from pydantic import BaseModel, Field

from .definition import GuidedConversationDefinition


class FormArtifact(BaseModel):
    title: str = Field(description="The title of the form.", default="")
    filename: str = Field(description="The filename of the form.", default="")


# Rules - These are the do's and don'ts that the agent should follow during the conversation.
rules = [
    "DO NOT suggest forms or create a form for the user.",
    "Politely request another file if the provided file is not a form.",
    "Terminate conversation if inappropriate content is requested.",
]

# Conversation Flow (optional) - This defines in natural language the steps of the conversation.
conversation_flow = """
1. Inform the user that our goal is for the user to provide a file that contains a form. The file can be PDF, TXT, or DOCX.
2. When you receive a file, determine if the file looks to be a form.
3. If the file is not a form, inform the user that the file is not a form. Ask them to provide a different file.
4. If the form is a file, update the artifcat with the title and filename of the form.
5. Inform the user that the form has been provided.
"""

# Context (optional) - This is any additional information or the circumstances the agent is in that it should be aware of.
# It can also include the high level goal of the conversation if needed.
context = """
"""

# Resource Constraints (optional) - This defines the constraints on the conversation such as time or turns.
# It can also help with pacing the conversation,
resource_constraint = ResourceConstraint(
    quantity=5,
    unit=ResourceConstraintUnit.MINUTES,
    mode=ResourceConstraintMode.MAXIMUM,
)

# Create instance of the GuidedConversationDefinition model with the above configuration.
definition = GuidedConversationDefinition(
    rules=rules,
    conversation_flow=conversation_flow.strip(),
    context=context.strip(),
    resource_constraint=resource_constraint,
    artifact=FormArtifact,
)
