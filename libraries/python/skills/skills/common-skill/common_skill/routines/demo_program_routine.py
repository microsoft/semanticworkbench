from textwrap import dedent

from skill_library import ProgramRoutine


def get_demo_program_routine(skill_name: str) -> ProgramRoutine:
    return ProgramRoutine(
        name="demo_program_routine",
        skill_name=skill_name,
        description="A demo program routine.",
        program=dedent("""
            result = common.web_search("{{stock_ticker}} stock price")
            cowboy = common.gpt_complete(f"Write this like a cowboy: {result}")
            posix.write_file("output.txt", cowboy)
            print(cowboy)
        """),
    )
