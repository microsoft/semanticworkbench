# Context

This library is shared among several different Make:Exploration projects including:

- [Skill Library](../skills/skill-library/README.md)

The [Context](./context/context.py) class in this library is designed to be
instantiated once and passed to all relevant parts of a system.

This is especially helpful in:

- Setting the **session id** for all parts of the system (allowing them all to
  share state in external state stores).
- Passing an `emit` function that all the parts can use for consistent event
  emitting. You can see an example of this in either of the projects listed
  above.
