"""
web research skill
"""

from typing import Any

from skill_library.routine.program_routine import ExternalFunctionMock, ProgramRoutine, get_function_source

# Program Routines store the source code for a routine that you would like
# executed. One way to provide that source code is to write a `main` function
# and then use `get_function_source` to get the source code of that function.
# This class is used to mock the functions that are called in the `main`
# function so it passes linting. Simply define any function that doesn't lint
# (which will be executed for real by the program_runner) and assign it a
# mock. This is good enough for being able to generate the source code for the
# routine.
posix: Any = ExternalFunctionMock
common: Any = ExternalFunctionMock()
ask_user: Any = ExternalFunctionMock()


# Define your routine function. We could use a string here, but it's better to
# use a function and then get the source code of that function so we can lint
# it.
def main():
    import json

    plan_name = "{{name}}"
    topic = "{{topic}}"
    plan = common.generate_research_plan(topic)
    posix.write_file(f"{plan_name}.txt", json.dumps(plan, indent=2))

    user_intent = "update"

    while user_intent == "update":
        ask_user("Does this plan look ok? If not, how would you like me to change it?")
        user_intent = common.select_user_intent({
            "confirm": "The user is happy with the plan and wants to execute it.",
            "update": "The user wants to change some things about the plan.",
            "exit": "The user wants to stop the research.",
        })
        if user_intent == "update":
            plan = common.update_research_plan(plan)
            posix.write_file(f"{plan_name}.txt", json.dumps(plan, indent=2))

    if user_intent == "exit":
        print("Exiting research.")
        posix.delete_file(f"{plan_name}.txt")
        return

    research_answers_filename = f"{plan_name}_research_answers.md"
    posix.touch(research_answers_filename)
    for step in plan:
        question = step["question"]
        good_answer = False
        query = question
        previous_searches = []
        while not good_answer:
            related_web_content = common.web_search(query, previous_searches)
            answer = common.answer_question_about_content(related_web_content, question)
            good_answer, reasoning = common.evaluate_answer(question, answer)
            if good_answer:
                posix.append_file(research_answers_filename, f"##{question}\\n\\n{answer}\\n\\n")
            else:
                previous_searches.append((query, reasoning))

    answers = posix.read_file(research_answers_filename)
    report = common.summarize(answers, topic)
    posix.write_file(f"{plan_name}_research_report.txt", report)
    print("Research complete.")


def get_deep_web_research_routine(skill_name: str) -> ProgramRoutine:
    return ProgramRoutine(
        name="deep_web_research_routine",
        skill_name=skill_name,
        description="Do a deep dive using the WWW on a given topic.",
        program=get_function_source(main),
    )
