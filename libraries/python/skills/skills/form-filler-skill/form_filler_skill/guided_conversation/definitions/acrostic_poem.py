from textwrap import dedent

from form_filler_skill.guided_conversation import UNANSWERED, TUnanswered
from form_filler_skill.guided_conversation.definition import GCDefinition
from form_filler_skill.guided_conversation.resources import (
    ResourceConstraint,
    ResourceConstraintMode,
    ResourceConstraintUnit,
)
from pydantic import BaseModel, Field


class Artifact(BaseModel):
    student_poem: str | TUnanswered = Field(description="The acrostic poem written by the student.", default=UNANSWERED)
    initial_feedback: str | TUnanswered = Field(
        description="Feedback on the student's final revised poem.", default=UNANSWERED
    )
    final_feedback: str | TUnanswered = Field(
        description="Feedback on how the student was able to improve their poem.", default=UNANSWERED
    )
    inappropriate_behavior: list[str] | TUnanswered = Field(
        description=dedent("""
                List any inappropriate behavior the student attempted while chatting with you.
                It is ok to leave this field Unanswered if there was none.
            """),
        default=UNANSWERED,
    )


definition = GCDefinition(
    artifact_schema=Artifact.model_json_schema(),
    rules=[
        "DO NOT write the poem for the student.",
        "Terminate the conversation immediately if the students asks for harmful or inappropriate content.",
    ],
    conversation_flow=dedent("""
        1. Start by explaining interactively what an acrostic poem is.
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
        4. Finally have the student write their own acrostic poem using the word or phrase of their choice. Encourage them
        to be creative and have fun with it. After they write it, you should review it and give them feedback on what they
        did well and what they could improve on. Have them revise their poem based on your feedback and then review it again.
    """),
    conversation_context=dedent("""
        You are working 1 on 1 a 4th grade student who is chatting with you in the computer lab at school while being
        supervised by their teacher.
    """),
    resource_constraint=ResourceConstraint(
        quantity=10,
        unit=ResourceConstraintUnit.TURNS,
        mode=ResourceConstraintMode.EXACT,
    ),
)
