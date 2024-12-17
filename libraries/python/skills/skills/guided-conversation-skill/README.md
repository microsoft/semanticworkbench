# Guided Conversation Skill

This functionality was originally written as a standalone assistant using
Semantic Kernel by the MAIDAP group.

This is a substantial rewrite for the Semantic Workbench skill framework as a
shareable, composable skill.

The original guided conversation code is a bit more complex than what is found
here because it has an action-choosing flow. This skill's revised routine is
simply:

```
if not first time:
    - updates = generate_artifact_updates
    - apply_updates(updates)
- agenda, done = generate_new_agenda
- if done:
    - artifact = generate_final_artifact
- else:
    - generate_message
```
