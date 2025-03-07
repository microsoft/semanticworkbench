from typing import Any, cast

from openai_client import (
    CompletionError,
    create_user_message,
    extra_data,
    format_with_liquid,
    make_completion_args_serializable,
    message_content_from_completion,
    validate_completion,
)
from skill_library import AskUserFn, EmitFn, RunContext, RunRoutineFn
from skill_library.logging import logger
from skill_library.skills.research2.research_skill import ResearchSkill

INITIAL_SYSTEM_PROMPT = """
Below I will present you a topic.

You will now build a comprehensive preparatory survey of which facts we have at our disposal and which ones we still need.
To do so, you will have to read the topic and identify things that must be discovered in order to successfully complete it.
Don't make any assumptions. For each item, provide a thorough reasoning. Here is how you will structure this survey:

---
### 1. Facts given in the topic
List here the specific facts given in the topic that could help you (there might be nothing here).

### 2. Facts to look up
List here any facts that we may need to look up.
Also list where to find each of these, for instance a website, a file... - maybe the topic contains some sources that you should re-use here.

### 3. Facts to derive
List here anything that we want to derive from the above by logical reasoning, for instance computation or simulation.

Keep in mind that \"facts\" will typically be specific names, dates, values, etc. Your answer should use the below headings:
### 1. Facts given in the task
### 2. Facts to look up
### 3. Facts to derive

Do not add anything else.

Here is the topic that all facts should relate to:

```
{{TOPIC}}
```

Now begin!
"""

UPDATE_SYSTEM_PROMPT = """
You will now build a comprehensive preparatory survey of which facts we have at our disposal and which ones we still need.

Earlier we've built a list of facts.

But since in your previous steps you may have learned useful new facts or invalidated some false ones.

Please update your list of facts based on the previous history, and provide these headings:

### 1. Facts given in the topic
### 2. Facts that we have learned
### 3. Facts still to look up
### 4. Facts still to derive

Do not add anything else.

Reminder, here is the topic that all facts should relate to:

```
{{TOPIC}}
```

Current plan:

```
{{PLAN}}
```

Here is the up-to-date list of facts that you know:

```
{{FACTS}}
```

Observations from previous research:

```
{{OBSERVATIONS}}
```

Update your list of facts. Now begin!
"""


async def main(
    context: RunContext,
    routine_state: dict[str, Any],
    emit: EmitFn,
    run: RunRoutineFn,
    ask_user: AskUserFn,
    topic: str,
    plan: str = "",
    facts: str = "",
    observations: list[str] = [],
) -> str:
    """Gather facts related to an ongoing research project based on observations we gather in the process of researching."""

    research_skill = cast(ResearchSkill, context.skills["research2"])
    language_model = research_skill.config.reasoning_language_model

    if not facts:
        prompt = format_with_liquid(INITIAL_SYSTEM_PROMPT, vars={"TOPIC": topic})
    else:
        all_observations = "\n- ".join(observations) if observations else ""
        prompt = format_with_liquid(
            UPDATE_SYSTEM_PROMPT, vars={"TOPIC": topic, "PLAN": plan, "FACTS": facts, "OBSERVATIONS": all_observations}
        )

    completion_args = {
        "model": "o1-mini",
        "messages": [
            create_user_message(
                prompt,
            ),
        ],
    }

    logger.debug("Completion call.", extra=extra_data(make_completion_args_serializable(completion_args)))
    metadata = {}
    metadata["completion_args"] = make_completion_args_serializable(completion_args)
    try:
        completion = await language_model.beta.chat.completions.parse(
            **completion_args,
        )
        validate_completion(completion)
        logger.debug("Completion response.", extra=extra_data({"completion": completion.model_dump()}))
        metadata["completion"] = completion.model_dump()
    except Exception as e:
        completion_error = CompletionError(e)
        metadata["completion_error"] = completion_error.message
        logger.error(
            completion_error.message,
            extra=extra_data({"completion_error": completion_error.body, "metadata": context.metadata_log}),
        )
        raise completion_error from e
    else:
        content = message_content_from_completion(completion).strip().strip('"')
        metadata["content"] = content
        return content
    finally:
        context.log("facts", metadata)
