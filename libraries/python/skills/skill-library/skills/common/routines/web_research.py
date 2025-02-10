"""
web research skill
"""

import json

from skill_library.engine import AskUserFn, PrintFn, RunContext


# Define your routine function. We could use a string here, but it's better to
# use a function and then get the source code of that function so we can lint
# it.
async def main(run_context: RunContext, ask_user: AskUserFn, print: PrintFn, plan_name: str, topic: str) -> str:
    posix = run_context.posix
    common = run_context.common

    plan = await common.generate_research_plan(topic)
    await posix.write_file(f"{plan_name}.txt", json.dumps(plan, indent=2))

    user_intent = "update"

    while user_intent == "update":
        ask_user("Does this plan look ok? If not, how would you like me to change it?")
        user_intent = await common.select_user_intent({
            "confirm": "The user is happy with the plan and wants to execute it.",
            "update": "The user wants to change some things about the plan.",
            "exit": "The user wants to stop the research.",
        })
        if user_intent == "update":
            plan = await common.update_research_plan(plan)
            posix.write_file(f"{plan_name}.txt", json.dumps(plan, indent=2))

    if user_intent == "exit":
        print("Exiting research.")
        posix.delete_file(f"{plan_name}.txt")
        return ""

    research_answers_filename = f"{plan_name}_research_answers.md"
    await posix.touch(research_answers_filename)
    for step in plan:
        question = step["question"]
        good_answer = False
        query = question
        previous_searches = []
        while not good_answer:
            related_web_content = await common.web_search(query, previous_searches)
            answer = await common.answer_question_about_content(related_web_content, question)
            good_answer, reasoning = await common.evaluate_answer(question, answer)
            if good_answer:
                await posix.append_file(research_answers_filename, f"##{question}\\n\\n{answer}\\n\\n")
            else:
                previous_searches.append((query, reasoning))

    answers = await posix.read_file(research_answers_filename)
    report = await common.summarize(answers, topic)
    await posix.write_file(f"{plan_name}_research_report.txt", report)
    print("Research complete.")
    return report
