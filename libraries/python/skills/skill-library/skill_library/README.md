# Skill Library

## Concepts

### Skills

Think of a skill as a package of assistant capabilities. A skill contains
"[routines](#routines)" that are entire procedures an assistant can run.

Using an everyday example in our own lives, you can imagine hiring a chef to
cook you a meal. The chef would be skilled at doing things in the kitchen (like
chopping or mixing or frying) and would also be able to execute full recipes,
allowing them to make particular dishes according to your preferences. All of
these actions can be encoded in a skill with routines.

A [Posix skill](./skills/posix/) (file system
interaction) is provided. Various routines are provided in the skill that
provide posix-like ability to manage a file system (creating directories and
files, listing files, reading files, etc.). In addition, though, a "compound"
routine (one that runs other routines) is provided that can create a user
directory with all of its associated sub directories.

We ship this and some other skill packages with the library
[here](./skills/), but you can import skill packages from
anywhere.

When a skill engine is registered to an assistant, a user will be able to see the
skill's routines by running the message command `/list_routines`.

See: [skill.py](./skill.py)

#### Routines

Routines are instructions that guide an agent to perform a program in a
prescribed manner, oftentimes in collaboration with users over many
interactions.

Implementation-wise, a routine is simply a Python module with a `main` function
that follows a particular signature. You put all the routines inside a `routine`
directory inside a skill package.

### Skill Engine

The `Engine` is the object that gets instantiated with all the running skills.
The engine can be asked to list or run any routine it has been configured with
and will do so in a managed "run context". The engine contains an "assistant
drive" that can be scoped to a specific persistence location to keep all the
state of the engine in one spot. The engine also handles the event handling for
all registered skills. Once an engine is started you can call (or subscribe to)
its `events` endpoint to get a list of generated events.

See: [engine.py](./engine.py), [Assistant Drive](../../../assistant-drive/README.md)

## State

The skill library provides multiple ways to manage state in an assistant.

### Drives

We use the [Assistant Drive](../../../assistant-drive/README.md) package to provide
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

See: [routine_stack.py](./routine_stack.py)
