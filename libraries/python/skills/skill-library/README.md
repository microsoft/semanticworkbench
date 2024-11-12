# Skill Library

This library allows you to create more capable chatbots, a.k.a. assistants. It
does this through the concept of a "skill".

Think of a skill as a package of assistant capabilities. A skill can contain
"actions" that an assistant can perform and "routines" that are entire
procedures that an assistant can run.

A demonstration [Posix skill](../skills/posix-skill/README.md) is provided that
makes these more clear. Various actions are provided in the skill that provide
posix-like ability to manage a file system (creating directories and files,
listing files, reading files, etc.). In addition, though, a routine is provided
that can create a user directory with all of it's associated sub directories.

Using an everyday example in our own lives, you can imagine hiring a chef to
cook you a meal. The chef would be skilled at actions in the kitchen (like
chopping or mixing or frying) but would also be able to perform full routines
(recipes), allowing them to make particular dishes according to your preferences.

In a way, this whole library was set up to be able to experiment with _routines_
more easily:

- This library hides a lot of the complexity of developing multi-layered
  assistants by providing clearer purposeful abstractions and better defining or
  disambiguating commonly confused terms. For example, we separate out a lot of
  the complexity of interacting with the OpenAI Chat Completion API with the
  [chat driver](../../openai-client/openai_client/chat_driver/README.md)
  abstraction and we now distinguish between chat commands, chat tool functions,
  and routine actions in a clear way, even though they're really all just
  functions.
- Routines (formerly referred to as "Recipes") make it clear that what we are
  developing agents that can automate productive work collaboratively with the
  user. We have several ideas here, from simply following a set of steps, to
  being able to run Pythonic programs skill actions, to much more fully managed
  routine running with LLM-driven meta-cognitive execution (having the LLM
  monitor progress and modify the routines as necessary).

Currently we provide one functional routine runner implementation, the
[InstructionRoutineRunner](./skill_library/routine_runners/instruction_routine_runner.py),
but will be adding several more in the upcoming weeks.

## Combining skills in the assistant

This library provides an [Assistant](./skill_library/assistant.py) class that
allows you to configure the conversational assistant (relying on our [chat
driver](../../chat-driver/README.md) library) and the skills that the
assistant should have.

Oftentimes, a truly capable assistant will need to have many skills.
Additionally, some skills are dependent upon other skills. When you register
skills to the assistant, the assistant will manage all their dependencies and
allow to you run any of their actions or routines.

When you run a skill routine, the assistant will manage the entire lifecycle of
that run for you.

You, as the assistant developer, can decide on the personality of your assistant
(setting the chat driver instructions), which commands you want to be able to
run as you are interacting with the assistant, and which tool functions you want
your assistant to be able to call on your behalf. These commands and tool
functions can include any of your assistant's skill's actions or routines.

This Assistant class can be easily wrapped inside our Semantic Workbench
assistant allowing it to be exposed as an assistant in the workbench. See our
[Semantic Workbench Skill
Assistant](../../../../assistants/skill-assistant/README.md)
package that does exactly this.

In the future, individual conversations might be handled in this library as
well.

## Context

This library uses the same [Context](../../context/README.md) library
as the [chat driver](../../chat-driver/README.md) library. This allows
you to instantiate a Context object for the assistant and have it automatically
passed into all assistant's actions and routines. This is especially helpful in
(1) setting the session id for all parts of the system (allowing them all to
share state in external state stores) and (2) passing and `emit` function that
all the parts can use to send events back up to the assistant for consistent
handling.

## More about Routines

### Experimentation

As mentioned above, one of the main purposes of this library is to make it
possible for an assistant to run a routine.

We are currently investigating different kinds of routine specifications and
ways of executing them.

Currently we provide one functional routine runner implementation, the
[InstructionRoutineRunner](./skill_library/routine_runners/instruction_routine_runner.py),
but will be adding several more in the upcoming weeks.

### Routines must be run from within an assistant

By design, routines can execute any action provided in any skill, not just their
own. This allows for composing and nesting multiple skills. Because of this, it
is not possible to simply instantiate a skill and run a routine within it (like
you can do with a skill's action). Routines can only be run from an
[Assistant](./skill_library/assistant.py) that has all dependent skills
registered to it.
