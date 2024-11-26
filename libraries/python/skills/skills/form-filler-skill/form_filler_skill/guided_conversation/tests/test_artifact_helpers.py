from typing import Any, Literal

from form_filler_skill.guided_conversation.artifact_helpers import artifact_from_schema
from pydantic import BaseModel


def test_artifact_from_schema():
    class TestSubSchema(BaseModel):
        field1: str
        field2: int

    class TestSchema(BaseModel):
        field1: str
        field2: int = 5  # Artifacts have no defaults. They're either answered or they're not.
        field3: float
        field4: list[str]
        field5: dict[str, Any]
        field6: TestSubSchema

    class SubSchema(BaseModel):
        field1: str | Literal["Unanswered"] = "Unanswered"
        field2: int | Literal["Unanswered"] = "Unanswered"

    class Artifact(BaseModel):
        field1: str | Literal["Unanswered"] = "Unanswered"
        field2: int | Literal["Unanswered"] = "Unanswered"
        field3: float | Literal["Unanswered"] = "Unanswered"
        field4: list[str] | Literal["Unanswered"] = "Unanswered"
        field5: dict[str, Any] | Literal["Unanswered"] = "Unanswered"
        field6: SubSchema | Literal["Unanswered"] = "Unanswered"

    actual_artifact_class = artifact_from_schema(TestSchema)
    # actual_artifact = actual_artifact_class()

    # assert actual_artifact.model_dump() == Artifact().model_dump()
    # assert Artifact.model_json_schema() == actual_artifact_class.model_json_schema()

    assert actual_artifact_class.model_fields.keys() == Artifact.model_fields.keys()
    for key in actual_artifact_class.model_fields.keys():
        if key != "field6":
            assert actual_artifact_class.model_fields[key].annotation == Artifact.model_fields[key].annotation
            assert actual_artifact_class.model_fields[key].default == Artifact.model_fields[key].default
            assert actual_artifact_class.model_fields[key].metadata == Artifact.model_fields[key].metadata
