# Skills

This is ongoing work by MADE:Exploration related to the idea of "recipes", now
more explicitly defined as "skills".

Skills allow you to create more capable chatbots, a.k.a. assistants.

This directory is split into:

- Our [skill library](./skill-library/README.md).
- A set of [skills](./skills/README.md) that can be run by the library.
- Jupyter [notebooks](./notebooks/README.md) that demonstrate using the skill
  library.

Also, see our
[example](../../../assistants/skill-assistant/README.md) of
integrating a skill [assistant](./skill-library/skill_library/assistant.py) into
a Semantic Workbench assistant if that's something you want to try.

Each of these are different python packages and will need to be installed
independently (using `make` or `poetry install` in their respective
directories).

## What is a "skill"?

Think of a skill as a package of assistant capabilities. A skill can contain
"actions" that an assistant can perform and "routines" that are entire
procedures that an assistant can run.

A demonstration [Posix skill](./skills/posix-skill/README.md) is provided that
makes these ideas more clear. Various actions are provided in the skill that provide
posix-like ability to manage a file system (creating directories and files,
listing files, reading files, etc.). In addition, though, a routine is provided
that can create a user directory with all of it's associated subdirectories.

Using an everyday example in our own lives, you can imagine hiring a chef to
cook you a meal. The chef would be skilled at actions in the kitchen (like
chopping or mixing or frying) but would also be able to perform full routines
(recipes), allowing them to make particular dishes according to your preferences.

## Skill Routines

In a way, this whole library was set up to be able to experiment with _routines_
more easily:

- This library hides a lot of the complexity of developing multi-layered
  assistants by providing clearer purposeful abstractions and better defining or
  disambiguating commonly confused terms. For example, we separate out a lot of
  the complexity of interacting with the OpenAI Chat Completion API with the
  [chat driver](../chat-driver/README.md) abstraction and we now
  distinguish between chat commands, chat tool functions, and routine actions in
  a clear way, even though they're really all just functions.
- Routines (formerly referred to as "Recipes") make it clear that what we are
  developing agents that can automate productive work collaboratively with the
  user. We have several ideas here, from simply following a set of steps, to
  being able to run Pythonic programs skill actions, to much more fully managed
  routine running with LLM-driven meta-cognitive execution (having the LLM
  monitor progress and modify the routines as necessary).

Currently we provide one functional routine runner implementation, the
[InstructionRoutineRunner](./skill-library/skill_library/routine_runners/instruction_routine_runner.py),
but will be adding several more in the upcoming weeks.
