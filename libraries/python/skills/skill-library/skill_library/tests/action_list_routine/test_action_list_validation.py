from textwrap import dedent

from skill_library.routine.action_list_routine import ActionListRoutine


def test_action_list_routine_validation():
    routine = ActionListRoutine(
        name="demo",
        skill_name="skill",
        description="A demo action list routine.",
        routine=dedent("""
            0: common.web_search("{{stock_ticker}} stock price")
            1: common.gpt_complete("Write this like a cowboy: {{0}}")
            2: posix.write_file("output.txt", {{1}})
            3: print([{{1}}])
        """),
    )

    vars = {"stock_ticker": "MSFT"}

    # Assert no exception thrown.
    assert routine.validate(vars) is None
