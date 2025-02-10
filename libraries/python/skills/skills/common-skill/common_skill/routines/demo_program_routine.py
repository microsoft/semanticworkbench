from skill_library.routine.program_routine import ExternalFunctionMock, ProgramRoutine, get_function_source

# Program Routines store the source code for a routine that you would like
# executed. One way to provide that source code is to write a `main` function
# and then use `get_function_source` to get the source code of that function.
# This class is used to mock the functions that are called in the `main`
# function so it passes linting. Simply define any function that doesn't lint
# (which will be executed for real by the program_runner) and assign it a
# mock. This is good enough for being able to generate the source code for the
# routine.
posix = ExternalFunctionMock()
common = ExternalFunctionMock()


# Define your routine function. We could use a string here, but it's better to
# use a function and then get the source code of that function so we can lint
# it.
def main():
    result = common.web_search("{{stock_ticker}} stock price")
    cowboy = common.gpt_complete(f"Write this like a cowboy: {result}")
    posix.write_file("output.txt", cowboy)
    print(cowboy)
    return cowboy


def get_demo_program_routine(skill_name: str) -> ProgramRoutine:
    return ProgramRoutine(
        name="demo_program_routine",
        skill_name=skill_name,
        description="A demo program routine.",
        program=get_function_source(main),
    )
