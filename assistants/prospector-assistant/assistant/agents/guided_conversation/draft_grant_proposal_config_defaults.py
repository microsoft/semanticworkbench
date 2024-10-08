from typing import List

from guided_conversation.utils.base_model_llm import BaseModelLLM
from guided_conversation.utils.resources import ResourceConstraint, ResourceConstraintMode, ResourceConstraintUnit
from pydantic import BaseModel, Field

# Introduction
# This configuration defines a guided conversation for assisting users in drafting a comprehensive grant proposal.
# The goal is to gather all necessary information systematically, validating and categorizing it as required,
# without actually drafting the proposal. The assistant's task is to ensure all required sections of the grant proposal
# are filled with accurate and relevant information provided by the user.


# Define the Grant Proposal Artifact
class DocumentDetail(BaseModel):
    section: str = Field(description="Section of the document.")
    content: str = Field(description="Content extracted from the document.")


class BudgetItem(BaseModel):
    category: str = Field(description="Category of the budget item.")
    amount: float = Field(description="Amount allocated for this item.")


class TeamMember(BaseModel):
    name: str = Field(description="Name of the team member.")
    role: str = Field(description="Role of the team member in the project.")


class Milestone(BaseModel):
    description: str = Field(description="Description of the milestone.")
    date: str = Field(description="Date of the milestone.")


class ArtifactModel(BaseModelLLM):
    # Grant Source Documents
    grant_source_document_list: List[str] = Field(description="List of provided source documents.")
    grant_requirements: List[DocumentDetail] = Field(
        description="Detailed requirements extracted from the source documents."
    )
    key_criteria: List[DocumentDetail] = Field(description="Important criteria and evaluation points for the grant.")

    # User Documents
    user_document_list: List[str] = Field(description="List of provided user documents.")
    extracted_details: List[DocumentDetail] = Field(
        description="Extracted information categorized by the types of details needed."
    )

    # Project Information
    project_title: str = Field(description="Title of the project.")
    project_summary: str = Field(description="A brief summary of the project.")
    project_objectives: List[DocumentDetail] = Field(description="Key objectives of the project.", default=[])
    project_methods: List[DocumentDetail] = Field(description="Methods and approaches to be used.", default=[])

    # Budget
    total_budget: float = Field(description="Total amount requested.")
    budget_breakdown: List[BudgetItem] = Field(description="Detailed budget breakdown.")

    # Team
    team_members: List[TeamMember] = Field(description="List of team members and their roles.")

    # Timeline
    start_date: str = Field(description="Proposed start date.")
    end_date: str = Field(description="Proposed end date.")
    milestones: List[Milestone] = Field(description="Key milestones and their dates.")

    # Additional Information
    additional_info: str = Field(description="Additional information from the user.")

    # Missing Information
    missing_info: str = Field(description="Information that is still missing.")

    # Final Details
    final_details: str = Field(description="Final details to complete the proposal.")


# Define the rules for the conversation
rules = [
    "Always ask clarifying questions if the information provided is ambiguous.",
    "Do not make assumptions about the user's responses.",
    "Ensure all required fields are filled before proceeding to the next step.",
    "Politely remind the user to provide missing information.",
    "Review all provided documents before requesting additional information.",
    "Do not share user's documents with others.",
    "Provide concise progress updates at key milestones or checkpoints, summarizing what has been collected and what "
    "is still needed.",
    "Limit responses to just what is needed to drive the next request from the user.",
    "Ensure that the data entered into the artifact matches the information provided by the user without modification.",
    "Ensure that all dates, amounts, and other data follow a consistent format as specified in the grant requirements.",
    "If the user indicates that they will provide a response later, set a reminder or follow-up at the end of the "
    "conversation.",
    "Gracefully handle any errors or invalid inputs by asking the user to correct or rephrase their responses.",
    "Prioritize critical information that is essential to the grant application before collecting additional details.",
    "Only proceed to the next section once the current section is fully completed.",
    "Provide a set of standardized responses or suggestions based on common grant proposal templates.",
    "Confirm all entered data with the user before finalizing the artifact.",
    "Ensure the assistant does not attempt to draft the proposal; focus solely on gathering and validating information.",
]

# Define the conversation flow
conversation_flow = """
1. Initial Greetings: Start with a friendly greeting and an overview of the process.
2. Request Grant Source Documents:
    1. Ask the user to provide any documents from the grant source.
    2. Extract and confirm necessary details from the provided documents.
3. Request User Documents:
    1. Ask the user to provide any of their own documents, notes, transcripts, etc. that might contain relevant information.
    2. Categorize the extracted details from the user documents.
4. Gather Project Information:
    1. Ask for the title of the project.
    2. Request a brief summary of the project.
    3. Collect key objectives of the project.
    4. Gather information on the methods and approaches to be used.
5. Collect Budget Details:
    1. Ask for the total amount requested for the project.
    2. Gather a detailed budget breakdown.
6. Collect Team Information:
    1. Ask for the names and roles of the project team members.
7. Determine Project Timeline:
    1. Ask for the proposed start date.
    2. Ask for the proposed end date.
    3. Collect key milestones and their dates.
8. Review and Suggest Additional Information:
    1. Review the provided documents.
    2. Suggest any additional information that might be needed.
9. Request Missing Information:
    1. Inform the user of what is still missing.
    2. Offer the opportunity to upload more documents or provide direct answers.
10. Finalize and Confirm:
    1. Walk through the remaining items one-by-one until all required information is gathered.
    2. Confirm all entered data with the user.
"""

# Provide context for the guided conversation
context = """
You are an AI assistant helping the user draft a comprehensive grant proposal. The goal is to gather all necessary
information systematically, validating and categorizing it as required, without actually drafting the proposal.
Your task is to ensure all required sections of the grant proposal are filled with accurate and relevant
information provided by the user.
"""

# Define the resource constraint
resource_constraint = ResourceConstraint(
    quantity=50,  # Number of turns
    unit=ResourceConstraintUnit.TURNS,
    mode=ResourceConstraintMode.EXACT,
)

__all__ = [
    "ArtifactModel",
    "rules",
    "conversation_flow",
    "context",
    "resource_constraint",
]
