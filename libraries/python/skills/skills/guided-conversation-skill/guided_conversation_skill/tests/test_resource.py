from guided_conversation_skill.resources import (
    GCResource,
    ResourceConstraintMode,
    ResourceConstraintUnit,
)


def test_resource_init_no_constraint() -> None:
    data = {}
    resource = GCResource.model_validate(data)
    assert resource.remaining_units == 0
    assert resource.elapsed_units == 0


def test_resource_init_with_constraint() -> None:
    data = {
        "resource_constraint": {
            "quantity": 10,
        },
    }
    resource = GCResource.model_validate(data)
    assert resource.resource_constraint is not None
    assert resource.resource_constraint.mode == ResourceConstraintMode.MAXIMUM
    assert resource.resource_constraint.unit == ResourceConstraintUnit.TURNS
    assert resource.elapsed_units == 0
    assert resource.remaining_units == 10.0

    resource.increment_resource()
    assert resource.elapsed_units == 1
    assert resource.remaining_units == 9


def test_resource_init() -> None:
    data = {
        "resource_constraint": {
            "quantity": 10,
            "mode": "maximum",
            "unit": "turns",
        },
        "turn_number": 3,
        "elapsed_units": 3,
        "remaining_units": 7,
        "initial_seconds_per_turn": 20,
    }
    resource = GCResource.model_validate(data)
    assert resource.resource_constraint is not None
    assert resource.resource_constraint.mode == ResourceConstraintMode.MAXIMUM
    assert resource.resource_constraint.unit == ResourceConstraintUnit.TURNS
    assert resource.elapsed_units == 3
    assert resource.remaining_units == 7
    assert resource.initial_seconds_per_turn == 20
    assert resource.turn_number == 3

    resource.increment_resource()

    assert resource.elapsed_units == 4
    assert resource.remaining_units == 6
    assert resource.turn_number == 4
