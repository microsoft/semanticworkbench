# tst_skill/routines/a_routine.py
from skill_library.engine import AskUserFn, PrintFn, RunContext


async def main(run_context: RunContext, ask_user: AskUserFn, print: PrintFn) -> str:
    # Call an action from the same skill
    await run_context.tst_skill.an_action()
    # Test asking user something
    response = await ask_user("test question")
    # Test printing something
    await print("test print")
    return response
