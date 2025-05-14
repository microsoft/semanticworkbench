# Comparison

## Comparing implementations

### Recipe Executor

- All input/output through context dict and files. Context mutation is opaque and buried in each step.
- Program flow through state machine flow diagram written in JSON. No Python available. Each step encodes its own.
- Sub-recipes through `execute_recipe` step.
- Control flow including `Loop` and `Conditional` steps.
- Packages recipes in sets (directories).
- No stack for running recipes (but one could be introduced to "see" where we are in control flow)
- "ask" handled by writing to files (how does resume work?)
- Interacts with the filesystem directly.
- Misc
  - More directly focused on driving LLMs. Includes tools for handling prompts and prompt context.

### Routine Library

- Input/output through python args. Transparent.
- Program flow through program written in Python. All non-external functions are available. No separate "steps".
- Subroutines through `run` function.
- Control flow using Python.
- Packages routines in skills (dynamically-loaded Python packages)
- A stack for running subroutines with variable scope (vs. a general context bucket).
- "ask" handled by pausing control flow, resumes with answer
- uses `Drive` for interacting with the filesystem.
- Misc
  - Focused on routines. LLM-agnostic.
