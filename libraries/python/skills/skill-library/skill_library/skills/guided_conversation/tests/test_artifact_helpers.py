# from skill_library.skills.guided_conversation.artifact_helpers import artifact_from_schema
from typing import Literal, get_type_hints

import jsonschema
import pytest
from skill_library.skills.guided_conversation.artifact_helpers import (
    InvalidArtifactFieldError,
    UpdateAttempt,
    validate_artifact_data,
    validate_field_value,
)
from skill_library.skills.guided_conversation.chat_completions.generate_artifact_updates import (
    ArtifactUpdate,
    validate_update_attempt,
)

# Resolve forward references in the validate_update_attempt function
validate_update_attempt.__annotations__ = get_type_hints(validate_update_attempt)

artifact_schema = {
    "properties": {
        "student_poem": {
            "type": "string",
            "default": "Unanswered",
            "description": "The acrostic poem written by the student.",
            "title": "Student Poem",
        },
        "initial_feedback": {
            "type": "string",
            "default": "Unanswered",
            "description": "Feedback on the student's final revised poem.",
            "title": "Initial Feedback",
        },
        "final_feedback": {
            "anyOf": [{"type": "string"}, {"const": "Unanswered", "type": "string"}],
            "default": "Unanswered",
            "description": "Feedback on how the student was able to improve their poem.",
            "title": "Final Feedback",
        },
        "inappropriate_behavior": {
            "anyOf": [{"items": {"type": "string"}, "type": "array"}],
            "default": "Unanswered",
            "description": "\nList any inappropriate behavior the student attempted while chatting with you.\nIt is ok to leave this field Unanswered if there was none.\n",
            "title": "Inappropriate Behavior",
        },
        "count": {
            "type": "integer",
            "default": "Unanswered",
            "description": "Count of something",
            "title": "Count",
        },
    },
    "title": "Artifact",
    "type": "object",
}

artifact_data = {
    "student_poem": "My poem",
    "initial_feedback": "Good job",
    "final_feedback": "Unanswered",
    "inappropriate_behavior": ["Inappropriate behavior"],
}


def test_validate_field_value():
    data = {
        "student_poem": "My poem",
        "initial_feedback": "Good job",
        "final_feedback": "Unanswered",
        "inappropriate_behavior": ["Inappropriate behavior"],
        "count": 1,
    }
    assert validate_field_value(artifact_schema, "count", data["count"]) == 1
    assert validate_field_value(artifact_schema, "student_poem", data["student_poem"]) == "My poem"
    assert (
        validate_field_value(artifact_schema, "inappropriate_behavior", data["inappropriate_behavior"])
        == data["inappropriate_behavior"]
    )


def test_validate_field_value_bad():
    data = {
        "student_poem": "My poem",
        "initial_feedback": "Good job",
        "final_feedback": "Unanswered",
        "inappropriate_behavior": ["Inappropriate behavior"],
        "count": "one",
    }
    with pytest.raises(jsonschema.ValidationError):
        assert validate_field_value(artifact_schema, "count", data["count"]) == 1


def test_validate_artifact_data_complete():
    data = {
        "student_poem": "My poem",
        "initial_feedback": "Good job",
        "final_feedback": "Whatever",
        "inappropriate_behavior": ["Inappropriate behavior"],
        "count": 1,
    }
    assert validate_artifact_data(artifact_schema, data) == data


def test_validate_artifact_data_incomplete():
    data = {
        "student_poem": "My poem",
        "final_feedback": "Whatever",
        "inappropriate_behavior": ["Inappropriate behavior"],
        "count": 1,
    }
    assert validate_artifact_data(artifact_schema, data) == data


@pytest.mark.parametrize(
    "update, expected_update_failure, error",
    [
        (ArtifactUpdate(field="student_poem", value_as_json="My poem"), None, None),
        (ArtifactUpdate(field="student_poem2", value_as_json="My poem"), None, InvalidArtifactFieldError()),
        (ArtifactUpdate(field="count", value_as_json="1"), None, None),
        (
            ArtifactUpdate(field="count", value_as_json="one"),
            UpdateAttempt(
                field_value="one",
                error='Parsed value is not the right type. Got `<class \'str\'>` but expected `{"type": "integer"}`.',
            ),
            None,
        ),
        (ArtifactUpdate(field="inappropriate_behavior", value_as_json='["Inappropriate behavior"]'), None, None),
    ],
)
def test_validate_update_attempt(
    update: ArtifactUpdate,
    expected_update_failure: UpdateAttempt | None | Literal["SKIP"],
    error: Exception | None,
):
    if error:
        with pytest.raises(type(error)):
            update_failure = validate_update_attempt(artifact_schema, update)
    else:
        update_failure = validate_update_attempt(artifact_schema, update)
        assert update_failure == expected_update_failure
