from textwrap import dedent

from .interpreter import FunctionCall, Interpreter


def test_interpreter():
    # Example Code
    code = dedent("""
    x = 5
    y = 10
    z = skill.action(x, y)  # External function call
    m = z + 3
    return m
    """)

    # Initialize and run the interpreter
    interpreter = Interpreter()
    interpreter.load_code(code)
    next = interpreter.run()

    assert interpreter.variables["x"] == 5
    assert interpreter.variables["y"] == 10
    assert interpreter.program_counter == 3
    assert interpreter.variables.get("z", -1) == -1

    assert isinstance(next, FunctionCall)
    assert next.func_name == "skill.action"
    assert next.args == (5, 10)

    next = interpreter.run(13)
    assert interpreter.variables["z"] == 13
    assert interpreter.variables["m"] == 16

    assert next == 16

    # To simulate resuming:
    # - Save the state before external function calls.
    # - Reload the state and continue execution after external results are available.
