from guided_conversation.utils.resources import ResourceConstraintMode, ResourceConstraintUnit
from pydantic import BaseModel, Field

from .definition import GuidedConversationDefinition, ResourceConstraintDefinition


class FormArtifact(BaseModel):
    title: str = Field(description="The title of the form.", default="")
    filename: str = Field(description="The filename of the form.", default="")


definition = GuidedConversationDefinition(
    rules=[
        "DO NOT suggest forms or create a form for the user.",
        "Politely request another file if the provided file is not a form.",
        "Terminate conversation if inappropriate content is requested.",
    ],
    conversation_flow=(
        """
        1. Inform the user that our goal is for the user to provide a file that contains a form. The file can be PDF, TXT, or DOCX.
        2. When you receive a file, determine if the file looks to be a form.
        3. If the file is not a form, inform the user that the file is not a form. Ask them to provide a different file.
        4. If the form is a file, update the artifcat with the title and filename of the form.
        5. Inform the user that the form has been provided.
        """
    ),
    context="",
    resource_constraint=ResourceConstraintDefinition(
        quantity=5,
        unit=ResourceConstraintUnit.MINUTES,
        mode=ResourceConstraintMode.MAXIMUM,
    ),
)
