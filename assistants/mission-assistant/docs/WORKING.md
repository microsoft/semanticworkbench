# Mission Assistant: Current Work Items

This document tracks items that are actively being worked on in the Mission Assistant project.

## In Progress

- **Field Request Resolution**: Bug in the HQ resolve_field_request tool usage
  - When HQ responds to a field request, the HQ assistant acknowledges it will resolve the request, but doesn't actually call the `resolve_field_request` tool function
  - Implemented a two-part solution:
    1. **Simplified Message Formatting**: Reduced the verbosity in prompts and displays
    2. **Added Smart Tool Enforcement**: Implemented keyword detection for resolution attempts which sets `tool_choice` to "auto"

- **Field Request Workflow**: Improving field request handling and resolution flow
  - Need to ensure field requests are consistently detected and properly resolved

- **Artifact Synchronization**: Enhancing reliability of file synchronization between conversations
  - Testing and verifying that artifacts consistently update across all linked conversations

## Next Up

- Test the field request resolution improvements in a live conversation
- Continue validating the field request workflow with larger-scale testing
- Verify that the inspector state updates properly when artifacts change