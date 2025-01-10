from pydantic import BaseModel
from skill_library.utilities import to_string


def test_to_string_none():
    value = to_string(None)
    assert value == ""


def test_to_string_str():
    value = to_string("hello")
    assert value == "hello"


def test_to_string_int():
    value = to_string(42)
    assert value == "42"


def test_to_string_float():
    value = to_string(3.14)
    assert value == "3.14"


def test_to_string_dict():
    value = to_string({"key": "value"})
    assert value == '{\n  "key": "value"\n}'


def test_to_string_list():
    value = to_string(["one", "two"])
    assert value == '[\n  "one",\n  "two"\n]'


def test_to_string_tuple():
    value = to_string(("one", "two"))
    assert value == '[\n  "one",\n  "two"\n]'


def test_to_string_pydantic_model():
    class Model(BaseModel):
        name: str = "base model"

    model = Model()
    value = to_string(model)
    assert value == '{\n  "name": "base model"\n}'
