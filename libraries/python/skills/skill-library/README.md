# Skill Library

This library allows you to create more capable chatbots, a.k.a. assistants,
a.k.a. agents. It does this through the concept of a "skill".

## Concepts

### Skills

Think of a skill as a package of assistant capabilities. A skill can contain
"[actions](#actions)" that an assistant can perform and
"[routines](#routines-and-routine-runners)" that are entire procedures (which use
actions) which an assistant can run.

Using an everyday example in our own lives, you can imagine hiring a chef to
cook you a meal. The chef would be skilled at actions in the kitchen (like
chopping or mixing or frying) but would also be able to perform full routines
(recipes), allowing them to make particular dishes according to your preferences.

A demonstration [Posix skill](../skills/posix-skill/README.md) (file system
interaction) is provided. Various actions are provided in the skill that provide
posix-like ability to manage a file system (creating directories and files,
listing files, reading files, etc.). In addition, though, a routine is provided
that can create a user directory with all of its associated sub directories.

To create a skill, a developer writes the skills actions and routines and puts
them in a [`Skill`](./skill_library/skill.py) class along with a
`SkillDefinition` used to configure the skill.

When a skill is registered to an assistant, a user will be able to see the
skill's actions by running the message command `/list_actions` and routines with
`/list_routines`.

The skill library helps in maintaining and distributing functionality with
skills as each skill is a separate Python package, however skills refer to other
skills using a [skill registry](#skill-registry).

See: [skill.py](./skill_library/skill.py)

#### Actions

Actions can be any Python function. Their only requirement is that they take a
[`RunContext`](#run-context) as their first argument.

See: [actions.py](./skill_library/actions.py)

#### Routines and Routine Runners

Routines are instructions that guide an agent to perform a set of actions in a
prescribed manner, oftentimes in collaboration with users over many
interactions. A routine and its routine runner is kindof like a recipe (routine)
for a chef (routine runner). The routine contains the instructions and the
runner is responsible for following those instructions.

We are experimenting with different ways to write routines. In this way,
routines are something like "Domain Specific Languages" (DSLs). Routine runners
need to be able to understand the "language" a routine is written in which is
why routine types and routine runners come in pairs.

Currently we provide three functional routine/routine runner implementations:

- [Instruction routine](./skill_library/routine/instruction_routine.py)
  ([Instruction routine runner](./skill_library/routine_runners/instruction_routine_runner.py)).

  Instruction routines contain a list of messages (natural language) to be sent
  to a skill's natural language endpoint (its chat driver). This was a
  first-attempt at writing routines and has limited value because it (currently)
  can only talk to the chat endpoint of the skill that contains this routine...
  and it can only run actions that are registered to the skill's chat driver.
  We're keeping this around only as an example, and in case it might be useful
  for something in the future.

- [Action List routine](./skill_library/routine/action_list_routine.py)
  ([Action List routine runner](./skill_library/routine_runners/action_list_routine_runner.py))

  Action List routines allow you to specify a list of actions (across all registered skills) for the assistant to take.  The results of previously-run actions can be used as arguments in actions allowing for the chaining of input/outputs.

- [State Machine routine](./skill_library/routine/state_machine_routine.py)
  ([State Machine routine runner](./skill_library/routine_runners/state_machine_routine_runner.py))

  State machine routines are very simple and defined solely by two functions:
  `init` and `step`. When a state machine routine is started, its `init` method
  is run. Then every message sent to the assistant will be routed to the the
  `step` method until the method indicates the routine is done. This is a
  technique used many developers when hard-coding advanced agent
  capabilities--changing some behind-the-scenes state in some way based on the
  messages received and juggling that state until an objective is achieved. It's
  not simple to reason through, and it can be difficult to code, but it works
  great. The [Guided Conversation skill
  routine](../skills/guided-conversation-skill/guided_conversation_skill/guided_conversation_skill.py)
  is a good example of this technique.

- [Program routine](./skill_library/routine/program_routine.py) ([Program
  routine
  runner](./skill_library/routine_runners/program/program_routine_runner.py))

  Write a routine in a subset of Python. Works now, but in development... will
  add more local function support, error handling, more assistant actions, etc.

- (Future) Recipes (natural language routines)

  We aim to create a type of routine that can be specified in more ordinary,
  everyday language, like a recipe for a chef. The recipe routine runner, then,
  will use LLMs to run these routines. We have a few ideas of how to implement
  this, perhaps translating the routine into a more specific type, or executing
  each step with a series of LLM calls (e.g., for intent, planning, and
  adaptation). Stay tuned.

### Skill Registry

By design, routines can execute any action provided in any skill, not just their
own. This allows for composing and nesting multiple skills. Because of this, it
is not possible to simply instantiate a skill and run a routine within it.
Routines can only be run from a [Skill
Registry](./skill_library/skill_registry.py) that has all dependent skills
registered to it.


When you run a skill routine, the skill registry will manage the entire lifecycle of
that run for you.

See: [skill_registry.py](./skill_library/skill_registry.py)

### Run Context

Through a `RunContext`, action functions have access to the useful utilities and
the current scope/context of the assistant and skill they are running within.
This allows the action developer to have access to the assistant state and be
able to run actions and routines from other skills, emit messages through the
assistant, etc.

See: [run_context.py](./skill_library/run_context.py)

### Assistant

The `Assistant` is the object that gets instantiated with all the running
skills. The assistant contains an "assistant drive" that can be scoped to a
specific persistence location to keep all the state of the assistant in one
spot. The assistant also handles the event handling for all registered skills.
Once an assistant is started you can call (or subscribe to) its `events`
endpoint to get a list of generated events.

See: [assistant.py](./skill_library/assistant.py), [Assistant Drive](../../assistant-drive/README.md)

#### Chat Driver

The Assistant's chat driver is the place to configure your assistant's natural
language interface.

You, as the assistant developer, can decide on the personality of your assistant
(setting the chat driver instructions), which commands you want to be able to
run as you are interacting with the assistant, and which tool functions you want
your assistant to be able to call on your behalf. These commands and tool
functions can include any of your assistant's skill's actions or routines.

See: [Chat Driver](../../openai-client/openai_client/chat_driver/README.md)

### Semantic Workbench integration

This Assistant class can be easily wrapped inside our Semantic Workbench
assistant allowing it to be exposed as an assistant in the workbench. See our
[Semantic Workbench Skill
Assistant](../../../../assistants/skill-assistant/README.md)
package that does exactly this.

The Skill Assistant handles the registration of skill library assistants and
routing events to and from the Workbench.

See: [Skill Assistant](../../../../assistants/skill-assistant/README.md)


## State

The skill library provides multiple powerful ways to manage state in an assistant.

### Drives

We use the [Assistant Drive](../../assistant-drive/README.md) package to provide
simple disk storage to components in the skill library. Each assistant is given
a drive (the "assistant drive") that should be "sub-drived" by all skills to use
as storage. This keeps all of the data together in one spot, making it easier to
copy/backup/clone/fork assistants.

### Routine Stack state

Even breaking drives down to the skill levels, trying to manage all state in
drives is somewhat like trying to store information in "global state" and has
similar problems... it introduces coupling between skills and routines in that
one routine needs to know where another routine stored specific information. As
complexity of the routines increases, this can result in an explosion of
complexity of routine configuration. To avoid this, we created the idea of a
"routine stack" which is managed by the skill registry's routine runner. Each
time a routine is run, an object to store state for that routine is created and
put on a stack for that routine run. If the routine calls a subroutine, another
frame is added to the stack for the new routine. Once the routine is completed,
the state object is removed from the run stack automatically. This allows each
routine to have its own state to be used for persistence of all variables
between runs (e.g. interactions with the user or switching focus to other
routines). Of course, a routine can still choose to save data in a drive or
another location, but putting it on the stack is a simple way to avoid more
complex configuration.

See: [routine_stack.py](./skill_library/routine_stack.py)

#### Using the routine stack

The routine stack is provided in the [run context](#run-context). Create a resource block using the stack inside of a routine or action like this:

```python
async with run_context.stack_frame_state() as state:
    state["some_variable_name"] = "some value"
```

The only thing to keep in mind is that when the resource block is exited,
everything in the state object will be serialized to disk, so make sure the
values you are assigning are serializable.

