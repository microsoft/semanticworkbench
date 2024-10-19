import json

from guided_conversation.utils.resources import ResourceConstraint, ResourceConstraintMode, ResourceConstraintUnit
from pydantic import BaseModel, Field

from ..definition import GuidedConversationDefinition


# Define nested models for emergency room triage
class PersonalInformation(BaseModel):
    name: str = Field(description="The full name of the patient in 'First Last' format.")
    sex: str = Field(description="Sex of the patient (M for male, F for female).")
    date_of_birth: str = Field(description="The patient's date of birth in 'MM-DD-YYYY' format.")
    phone: str = Field(description="The patient's primary phone number in 'XXX-XXX-XXXX' format.")


class Artifact(BaseModel):
    personal_information: PersonalInformation = Field(
        description="The patient's personal information, including name, sex, date of birth, and phone."
    )
    chief_complaint: str = Field(description="The main reason the patient is seeking medical attention.")
    symptoms: list[str] = Field(description="List of symptoms the patient is currently experiencing.")
    medications: list[str] = Field(description="List of medications the patient is currently taking.")
    medical_history: list[str] = Field(description="Relevant medical history including diagnoses, surgeries, etc.")
    esi_level: int = Field(description="The Emergency Severity Index (ESI) level, an integer between 1 and 5.")
    resource_needs: list[str] = Field(description="A list of resources or interventions needed.")


# Rules - Guidelines for triage conversations
rules = [
    "DO NOT provide medical advice.",
    "Terminate the conversation if inappropriate content is requested.",
    "Begin by collecting basic information such as name and date of birth to quickly identify the patient.",
    "Prioritize collecting the chief complaint and symptoms to assess the immediate urgency.",
    "Gather relevant medical history and current medications that might affect the patient's condition.",
    "If time permits, inquire about additional resource needs for patient care.",
    "Maintain a calm and reassuring demeanor to help put patients at ease during questioning.",
    "Focus questions to ensure the critical information needed for ESI assignment is collected first.",
    "Move urgently but efficiently through questions to minimize patient wait time during triage.",
    "Ensure confidentiality and handle all patient information securely.",
]

# Conversation Flow - Steps for the triage process
conversation_flow = """
1. Greet the patient and explain the purpose of collecting medical information for triage, quickly begin by collecting basic identifying information such as name and date of birth.
2. Ask about the chief complaint to understand the primary reason for the visit.
3. Inquire about current symptoms the patient is experiencing.
4. Gather relevant medical history, including past diagnoses, surgeries, and hospitalizations.
5. Ask the patient about any medications they are currently taking.
6. Determine if there are any specific resources or interventions needed immediately.
7. Evaluate the collected information to determine the Emergency Severity Index (ESI) level.
8. Reassure the patient and inform them of the next steps in their care as quickly as possible.
"""

# Context - Additional information for the triage process
context = """
Assisting patients in providing essential information during emergency room triage in a medical setting.
"""

# Resource Constraints - Defines the constraints like time for the conversation
resource_constraint = ResourceConstraint(
    quantity=10,
    unit=ResourceConstraintUnit.MINUTES,
    mode=ResourceConstraintMode.MAXIMUM,
)

# Create instance of the GuidedConversationDefinition model with the above configuration.
er_triage = GuidedConversationDefinition(
    artifact=json.dumps(Artifact.model_json_schema(), indent=2),
    rules=rules,
    conversation_flow=conversation_flow,
    context=context,
    resource_constraint=GuidedConversationDefinition.ResourceConstraint(
        quantity=10,
        unit=ResourceConstraintUnit.MINUTES,
        mode=ResourceConstraintMode.MAXIMUM,
    ),
)
