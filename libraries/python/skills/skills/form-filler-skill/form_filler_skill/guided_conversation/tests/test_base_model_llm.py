from form_filler_skill.guided_conversation.base_model_llm import BaseModelLLM


def test_parse_literal_eval():
    # Test that the parse_literal_eval method correctly parses the value
    # returned by the LLM to the correct type.
    class TestModel(BaseModelLLM):
        int_field: int
        none_field: None
        float_field: float
        bool_field: bool
        # list_field: list[str]
        # dict_field: dict[str, str]
        str_field: str

    test_model = TestModel(
        int_field="1",  # type: ignore
        none_field="None",  # type: ignore
        float_field="1.0",  # type: ignore
        bool_field="True",  # type: ignore
        # list_field='["x", "y"]',
        # dict_field='{"x": "y"}',
        str_field="x",
    )

    assert test_model.int_field == 1
    assert test_model.none_field is None
    assert test_model.float_field == 1.0
    assert test_model.bool_field is True
    # assert test_model.list_field == ["x", "y"]
    # assert test_model.dict_field == {"x": "y"}
    assert test_model.str_field == "x"
