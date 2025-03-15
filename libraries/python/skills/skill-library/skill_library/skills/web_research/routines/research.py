"""
web research skill
"""

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
    max_steps: int = 5,
) -> None:
    """Research a topic thoroughly and return a report."""

    steps = 0
    facts = await run("web_research.facts", topic=topic)
    plan, done = await run("web_research.search_plan", topic=topic)
    observations = []
    while not done:
        if steps > max_steps:
            break
        steps += 1

        urls = await run("web_research.search", topic=topic, plan=plan, facts=facts, observations=observations)

        observation = await run(
            "web_research.visit_pages", urls=urls, topic=topic, plan=plan, facts=facts, observations=observations
        )
        observations.append(observation)

        facts = await run("web_research.facts", topic=topic, plan=plan, facts=facts, observations=observations)

        plan, done = await run(
            "web_research.search_plan", topic=topic, plan=plan, facts=facts, observations=observations
        )

    final_report = await run(
        "web_research.make_final_report", topic=topic, plan=plan, facts=facts, observations=observations
    )

    await run("posix.write_file", f"{plan_name}.txt", final_report)
    return final_report
