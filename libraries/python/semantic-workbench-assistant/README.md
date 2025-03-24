# Semantic Workbench Assistant

Base class and utilities for creating an assistant within the Semantic Workbench.

## Assistant Templates

The Semantic Workbench supports assistant templates, allowing assistant services to provide multiple types of assistants with different configurations. Each template includes a unique ID, name, description, and default configuration. When users create a new assistant, they select from available templates rather than configuring an assistant from scratch.

To implement templates for your assistant service, define them in your service configuration and return them as part of your service info response.

## Start canonical assistant

The repository contains a canonical assistant without any AI features, that can be used as starting point to create custom agents.

To start the canonical assistant:

```sh
cd workbench-service
start-assistant semantic_workbench_assistant.canonical:app
```
