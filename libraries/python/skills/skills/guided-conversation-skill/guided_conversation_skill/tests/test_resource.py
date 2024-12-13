from guided_conversation_skill.resources import GCResource, ResourceConstraintMode, ResourceConstraintUnit


async def test_resource_init() -> None:
    data = {
        "resource_constraint": {
            "mode": "maximum",
            "unit": "turns",
            "quantity": 10,
        },
        "turn_number": 3,
        "elapsed_unit": 3.0,
        "remaining_units": 4.0,
        "initial_seconds_per_turn": 120,
    }
    resource = GCResource(**data)
    assert resource.resource_constraint is not None
    assert resource.resource_constraint.mode == ResourceConstraintMode.MAXIMUM
    assert resource.resource_constraint.unit == ResourceConstraintUnit.TURNS
