from textwrap import dedent

from skill_library import ActionListRoutine


def get_demo_routine(skill_name: str) -> ActionListRoutine:
    return ActionListRoutine(
        name="demo",
        skill_name=skill_name,
        description="A demo action list routine.",
        routine=dedent("""
            0: common.web_search("{{stock_ticker}} stock price")
            1: common.gpt_complete("Write this like a cowboy: {{0}}")
            2: posix.write_file("output.txt", "{{1}}")
            3: print("{{1}}")
        """),
    )
