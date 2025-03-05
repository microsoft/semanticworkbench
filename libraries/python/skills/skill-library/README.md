# MADE Explorations Skill Library

## Overview

This library allows you to create more capable agentic flows that can be used in
chatbots, a.k.a. assistants, a.k.a. agents, MCP servers, command line utilities
or any system that needs the ability to run composable, interactive agentic
workflows.

Skills are collections of routines that enable multi-step, interactive flows in
a given domain. Skills are really just a way to organize and package routines.

Read more about the concepts behind the library in the [skill library
README](./skill_library/README.md).

## Routines

Some [skill packages](./skill_library/skills/) with various routines are
provided in the skill library as a convenience. But you can bring your own skill
packages and register them with the skill engine if you'd like. Read more in the
[skill library README.md](./skill_library/README.md).

## Semantic Workbench integration

This Engine class can be easily wrapped inside our Semantic Workbench
assistant. See our
[Semantic Workbench Skill
Assistant](../../../../assistants/skill-assistant/README.md)
package that does exactly this.

The Skill Assistant handles the registration of skill library assistants and
routing events to and from the Workbench.

See: [Skill Assistant](.../../../../assistants/skill-assistant/README.md)

## MCP integration

An [MCP server](../../../../mcp-servers/mcp-server-web-research/README.md) has
been created that runs just a single routine, the
[research2.research](./skill_library/skills/research2/routines/research.py)
routine. We may enable this MCP server to run more routines in the future.

## Command line integration

We have also created a [command line utility](./skill_library/cli/README.md)
that allows any routine to be run from the command line. In non-interactive mode
(not requiring the `ask_user` function), routines can be piped like any command
line program. If the routine requires user interaction, it can be run directly
(without piping) and the command line will be used like a conversational window.

## Using chatbots to generate routines

Our meta-skill containes a
[generate_routine](./skill_library/skills/meta/routines/generate_routine.py)
routine that can help generate a new routine. It references the
[llm_info.txt](./skill_library/llm_info.txt) file which can also be used
directly in a chatbot of your choice as context for generating routines.

To have your generated routine reference your other routines and skill
configuration, you'll need to add that as context (the generate_routine routine
does this for you).
