"""
web research skill
"""

import json
from typing import Any

from skill_library import AskUserFn, EmitFn, RunContext, RunRoutineFn


async def main(
    context: RunContext,
    routine_state: dict[str, Any],
    emit: EmitFn,
    run: RunRoutineFn,
    ask_user: AskUserFn,
    plan_name: str,
    topic: str,
) -> str:
    """Research a topic thoroughly and return a report."""
    plan = await run("research.generate_research_plan", topic)
    await run("posix.write_file", f"{plan_name}.txt", json.dumps(plan, indent=2))

    user_intent = "update"

    while user_intent == "update":
        await ask_user("Does this plan look ok? If not, how would you like me to change it?")
        user_intent = await run(
            "common.select_user_intent",
            {
                "confirm": "The user is happy with the plan and wants to execute it.",
                "update": "The user wants to change some things about the plan.",
                "exit": "The user wants to stop the research.",
            },
        )
        if user_intent == "update":
            plan = json.loads(await run("posix.read_file", f"{plan_name}.txt"))
            plan = await run("research.update_research_plan", topic, plan)
            await run("posix.write_file", f"{plan_name}.txt", json.dumps(plan, indent=2))

    if user_intent == "exit":
        print("Exiting research.")
        await run("posix.delete_file", f"{plan_name}.txt")
        return ""

    plan = json.loads(await run("posix.read_file", f"{plan_name}.txt"))
    research_answers_filename = f"{plan_name}_research_answers.md"
    await run("posix.write_file", research_answers_filename, f"# Research on {topic}\n\n")
    for question in plan:
        is_good_answer = False
        query = question
        previous_searches = []
        while not is_good_answer:
            related_web_content = await run(
                "research.web_search", search_description=query, previous_searches=previous_searches
            )
            answer = await run("research.answer_question_about_content", related_web_content, question)
            is_good_answer, reasoning = await run("research.evaluate_answer", question, answer)
            if is_good_answer:
                await run("posix.append_file", research_answers_filename, f"## {question}\n\n{answer}\n\n")
            else:
                previous_searches.append((query, reasoning))

    answers = await run("posix.read_file", research_answers_filename)
    conclusion = await run("common.summarize", answers, topic)
    await run("posix.append_file", research_answers_filename, f"## Conclusion\n\n{conclusion}\n\n")

    return conclusion
