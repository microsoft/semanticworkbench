from skill_library.routine_runners.program_routine_runner import Interpreter, ReturnValue


def test_injectiong_json_library():
    """You can use libraries that are available in the interpreter's
    environment. Just import them inside your main function.
    """
    interpreter = Interpreter()

    def main():
        import json

        x = {"key": "value"}
        return json.dumps(x)

    interpreter = Interpreter().load_function(main)
    gen = interpreter.execute_with_pausing()
    result = next(gen)
    assert isinstance(result, ReturnValue)
    assert result.value == '{"key": "value"}'
