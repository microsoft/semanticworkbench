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
from skill_library.skills.web_research.research_skill import WebResearchSkill

INITIAL_SYSTEM_PROMPT = """
Below I will present you a topic for research.

Your job is to build a comprehensive and accurate inventory of facts related to this topic.

Structure your response as follows:

### 1. Facts given in the topic
List the specific, verifiable facts explicitly stated in the topic description.

### 2. Facts to look up
List specific information that needs to be researched, focusing on:
- Technical details and specifications
- Verified data from authoritative sources
- Expert opinions from trusted reviewers
- Genuine user experiences and feedback
For each fact, suggest potential high-quality sources (e.g., official documentation, academic papers, specialized forums) and avoid SEO-optimized content.

### 3. Facts to derive
List conclusions that can be drawn through logical reasoning based on verified information.

Here is the topic:

```
{{TOPIC}}
```
"""

UPDATE_SYSTEM_PROMPT = """
You are updating your fact inventory based on new research. Be rigorous about distinguishing between:
- Verified facts (with identified sources)
- Inferred information (clearly marked)
- Information gaps (explicitly acknowledged)

Structure your response as follows:

### 1. Facts given in the topic
List only explicit facts from the original topic.

### 2. Facts we have verified
For each fact, include:
- The specific information learned
- The source it came from
- A confidence rating (High/Medium/Low)

### 3. Facts still to look up
Be specific about remaining information gaps and potential sources.

### 4. Facts still to derive
List conclusions that could be drawn with additional information.

Topic:

```
{{TOPIC}}
```

Current plan:

```
{{PLAN}}
```

Current facts:

```
{{FACTS}}
```

Observations:

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

    research_skill = cast(WebResearchSkill, context.skills["web_research"])
    language_model = research_skill.config.reasoning_language_model

    if not facts:
        prompt = format_with_liquid(INITIAL_SYSTEM_PROMPT, vars={"TOPIC": topic})
    else:
        all_observations = "\n- ".join(observations) if observations else ""
        prompt = format_with_liquid(
            UPDATE_SYSTEM_PROMPT, vars={"TOPIC": topic, "PLAN": plan, "FACTS": facts, "OBSERVATIONS": all_observations}
        )

    completion_args = {
        "model": "o3-mini",
        "reasoning_effort": "high",
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
