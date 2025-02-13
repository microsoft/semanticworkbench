"""
web research skill
"""

import json

from skill_library import RunContext
from skill_library.types import AskUserFn, EmitFn, GetStateFn, PrintFn, RunActionFn, RunRoutineFn, SetStateFn


# Define your routine function. We could use a string here, but it's better to
# use a function and then get the source code of that function so we can lint
# it.
async def main(
    context: RunContext,
    ask_user: AskUserFn,
    print: PrintFn,
    run_action: RunActionFn,
    run_routine: RunRoutineFn,
    get_state: GetStateFn,
    set_state: SetStateFn,
    emit: EmitFn,
    plan_name: str,
    topic: str,
) -> str:
    plan, _ = await run_action("common.generate_research_plan", topic)
    await run_action("posix.write_file", f"{plan_name}.txt", json.dumps(plan, indent=2))

    user_intent = "update"

    while user_intent == "update":
        await ask_user("Does this plan look ok? If not, how would you like me to change it?")
        user_intent = await run_action(
            "common.select_user_intent",
            {
                "confirm": "The user is happy with the plan and wants to execute it.",
                "update": "The user wants to change some things about the plan.",
                "exit": "The user wants to stop the research.",
            },
        )
        if user_intent == "update":
            plan, _ = await run_action("common.update_research_plan", plan)
            await run_action("posix.write_file", f"{plan_name}.txt", json.dumps(plan, indent=2))

    if user_intent == "exit":
        print("Exiting research.")
        await run_action("posix.delete_file", f"{plan_name}.txt")
        return ""

    research_answers_filename = f"{plan_name}_research_answers.md"
    await run_action("posix.touch", research_answers_filename)
    for question in plan:
        is_good_answer = False
        query = question
        previous_searches = []
        while not is_good_answer:
            related_web_content = await run_routine(
                "common.web_search", search_description=query, previous_searches=previous_searches
            )
            answer, _ = await run_action("common.answer_question_about_content", related_web_content, question)
            is_good_answer, reasoning = await run_action("common.evaluate_answer", question, answer)
            if is_good_answer:
                await run_action("posix.append_file", research_answers_filename, f"##{question}\\n\\n{answer}\\n\\n")
            else:
                previous_searches.append((query, reasoning))

    answers = await run_action("posix.read_file", research_answers_filename)
    report = await run_action("common.summarize", answers, topic)
    await run_action("posix.write_file", f"{plan_name}_research_report.txt", report)
    print("Research complete.")
    return report
