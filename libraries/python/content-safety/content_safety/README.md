# Content Safety Module Internal Structure

This directory contains the implementation of content safety evaluators for the Semantic Workbench.

## Directory Structure

- `evaluators/` - Base evaluator interfaces and implementations
  - `azure_content_safety/` - Azure Content Safety API implementation
  - `openai_moderations/` - OpenAI Moderations API implementation

## Implementation Details

The module is designed with a plugin architecture to support multiple content safety providers:

1. Each provider has its own subdirectory with:
   - `evaluator.py` - Implementation of the ContentSafetyEvaluator interface
   - `config.py` - Pydantic configuration model with UI annotations
   - `__init__.py` - Exports for the module

2. The `CombinedContentSafetyEvaluator` serves as a factory that:
   - Takes a configuration that specifies which provider to use
   - Instantiates the appropriate evaluator based on the configuration
   - Delegates evaluation requests to the selected provider

This architecture makes it easy to add new providers while maintaining a consistent API.
