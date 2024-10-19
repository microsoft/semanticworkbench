import json

from guided_conversation.utils.resources import ResourceConstraint, ResourceConstraintMode, ResourceConstraintUnit
from pydantic import BaseModel, Field

from .definition import GuidedConversationDefinition


# Artifact - The artifact is like a form that the agent must complete throughout the conversation.
# It can also be thought of as a working memory for the agent.
# We allow any valid Pydantic BaseModel class to be used.
# Define nested models for personal information
class PersonalInformation(BaseModel):
    name: str = Field(description="The full name of the patient.")
    date_of_birth: str = Field(
        description="The patient's date of birth in 'MM-DD-YYYY' format.",
    )
    phone_number: str = Field(
        description="The patient's phone number in 'XXX-XXX-XXXX' format.",
    )
    email: str = Field(description="The patient's email address.")


class PatientIntakeArtifact(BaseModel):
    personal_information: PersonalInformation = Field(
        description="The patient's personal information, including name, date of birth, phone number, and email."
    )
    list_of_symptoms: list[dict] = Field(description="List of symptoms with details and affected area.")
    list_of_medications: list[dict] = Field(description="List of medications with name, dosage, and frequency.")


# Rules - These are the do's and don'ts that the agent should follow during the conversation.
rules = ["DO NOT provide medical advice.", "Terminate conversation if inappropriate content is requested."]

# Conversation Flow (optional) - This defines in natural language the steps of the conversation.
conversation_flow = """
1. Inform the patient that the information collected will be shared with their doctor.
2. Collect the patient's personal information, including their full name, date of birth, phone number, and email address.
3. Ask the patient about any symptoms they are experiencing and record the details along with the affected area.
4. Inquire about any medications, including the name, dosage, and frequency, that the patient is currently taking.
5. Confirm with the patient that all symptoms and medications have been reported.
6. Advise the patient to wait for their doctor for any further consultation or questions.
"""

# Context (optional) - This is any additional information or the circumstances the agent is in that it should be aware of.
# It can also include the high level goal of the conversation if needed.
context = """
You are an AI assistant that runs the new patient intake process at a doctor's office.
The purpose is to collect comprehensive information about the patient's symptoms, medications, and personal details.
This data will be shared with the doctor to facilitate a thorough consultation. The interaction is conducted in a respectful
and confidential manner to ensure patient comfort and compliance.
"""

# Resource Constraints (optional) - This defines the constraints on the conversation such as time or turns.
# It can also help with pacing the conversation,
# For example, here we have set an exact time limit of 10 turns which the agent will try to fill.
resource_constraint = ResourceConstraint(
    quantity=15,
    unit=ResourceConstraintUnit.MINUTES,
    mode=ResourceConstraintMode.MAXIMUM,
)

# Create instance of the GuidedConversationDefinition model with the above configuration.
patient_intake = GuidedConversationDefinition(
    artifact=json.dumps(PatientIntakeArtifact.model_json_schema(), indent=2),
    rules=rules,
    conversation_flow=conversation_flow.strip(),
    context=context.strip(),
    resource_constraint=GuidedConversationDefinition.ResourceConstraint(
        quantity=15,
        unit=ResourceConstraintUnit.MINUTES,
        mode=ResourceConstraintMode.MAXIMUM,
    ),
)
