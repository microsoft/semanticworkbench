from typing import Annotated

from pydantic import BaseModel, Field
from semantic_workbench_assistant.config import UISchema

from .definition import GuidedConversationDefinition
from .definitions.er_triage import er_triage
from .definitions.interview import interview
from .definitions.patient_intake import patient_intake
from .definitions.poem_feedback import poem_feedback

#
# region Models
#


class GuidedConversationAgentConfigModel(BaseModel):
    definition: Annotated[
        GuidedConversationDefinition,
        Field(
            title="Definition",
            description="The definition of the guided conversation agent.",
        ),
        UISchema(
            schema={
                "ui:options": {
                    "configurations": {
                        "Poem Feedback": poem_feedback.model_dump(mode="json"),
                        "Interview": interview.model_dump(mode="json"),
                        "Patient Intake": patient_intake.model_dump(mode="json"),
                        "ER Triage": er_triage.model_dump(mode="json"),
                    },
                },
            },
        ),
    ] = poem_feedback


# endregion
