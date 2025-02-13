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

When a skill engine is registered to an assistant, a user will be able to see the
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

### Skill Engine

The `Engine` is the object that gets instantiated with all the running
skills. The engine contains an "assistant drive" that can be scoped to a
specific persistence location to keep all the state of the engine in one
spot. The engine also handles the event handling for all registered skills.
Once an engine is started you can call (or subscribe to) its `events`
endpoint to get a list of generated events.

See: [engine.py](./skill_library/engine.py), [Assistant Drive](../../assistant-drive/README.md)

### Semantic Workbench integration

This Engine class can be easily wrapped inside our Semantic Workbench
assistant. See our
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
simple disk storage to components in the skill library. Each engine is given
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

## User scenario

Let me walk through the expected flow:

1. The initial `/run_routine` command hits `on_command_message_created` in skill_assistant.py
   - It parses the command and calls ChatFunctions.run_routine
   - This calls engine.run_routine with "common.web_research" and the parameters
   - Engine creates a task to run the routine and returns a future
   - ChatFunctions awaits this future

2. The routine starts executing:
   - Makes a research plan using common.generate_research_plan
   - Writes it to a file
   - Then hits the first `ask_user` call with "Does this plan look ok?"
   - This creates a MessageEvent with that prompt
   - The routine pauses, waiting for input via the input_future

3. When the user sends their response (like "Yes, looks good"):
   - That message hits `on_message_created` in skill_assistant.py
   - It checks `is_routine_running()` which should return true because we have a current_routine
   - It calls `resume_routine` with the user's message
   - This sets the result on the input_future
   - The routine continues executing from where it was paused at ask_user

4. This cycle repeats for any other ask_user calls in the routine:
   - Routine pauses at ask_user
   - User responds
   - Message gets routed to resume_routine
   - Routine continues

5. Finally when the routine completes:
   - It sets its final result on the result_future
   - Cleans up (current_routine = None)
   - The original run_routine future completes

The key points are:

1. While a routine is running, ALL messages should be routed to resume_routine
2. The routine's state (current_routine) needs to persist between messages
3. The futures mechanism lets us pause/resume the routine while keeping it "alive"

Looking at this flow, I suspect our issue might be that we're not properly maintaining the routine's state between messages. Let's verify the routine is still considered "running" when we get the user's response.
