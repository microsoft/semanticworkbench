# Semantic Workbench Assistant Development Guide

## Overview

For assistants to be instantiated in Semantic Workbench, you need to implement an assistant service that the workbench can talk with via http.
We provide several python base classes to make this easier: [semantic-workbench-assistant](../semantic-workbench/v1/service/semantic-workbench-assistant/README.md)

Example assistant services:

- [Canonical assistant example](../semantic-workbench/v1/service/semantic-workbench-assistant/semantic_workbench_assistant/canonical.py)
- .NET agent [example 1](../examples/dotnet-example01/README.md) and [example 2](../examples/dotnet-example02/README.md)

## Top level concepts

### assistant_service.FastAPIAssistantService

Your main job is to implement a service that supports all the Semantic Workbench methods. The [Canonical assistant example](../semantic-workbench/v1/service/semantic-workbench-assistant/semantic_workbench_assistant/canonical.py) demonstrates a minimal implementation.

It implements an assistant service that inherits from FastAPIAssistantService:

`class CanonicalAssistant(assistant_service.FastAPIAssistantService):`

This service is now a FastAPIAssistantService containing all the assistant methods that can be overridden as desired.

## Node Engine assistants

Though not mandatory, you might find it helpful to use the [Node Engine](https://github.com/microsoft/nodeengine) for creating assistants.
Node Engine gives you utilities for defining complex LLM interactions using a flow-based architecture where a "context" is modified through several flow components.
We have provided a NodeEngineAssistant base class that makes using the Node Engine simpler.

### Inheriting BaseNodeEngineAssistantInstance in your AssistantInstanceModel

You need to create an instance model for your assistant, e.g. `AssistantInstanceModel`.
It should implement the `node_engine_assistant.BaseAssistantInstance` Pydantic model and ABC.
This Pydantic model holds the id, assistant_name, config, and conversations attributes and the ABC ensures that my assistant sets up `config`, implements a `construct` factory static method, and a `config_ui_schema` static method.
These static methods are used by the workbench service.

Your assistant (service) should inherit `BaseNodeEngineAssistant` typed as my `AssistantInstanceModel`.
For example:

```jsx
MyAssistant(
  node_engine_assistant.BaseNodeEngineAssistant[AssistantInstanceModel]
):
```

`BaseNodeEngineAssistant` is an ABC generic for any type that inherits from `BaseAssistantInstance` (like my `AssistantInstanceModel`).
This class inherits `assistant_service.FastAPIAssistantService` which is an ABC for all the service methods.
`assistant_service_api(app: FastAPI, service: FastAPIAssistantService)` is a function that configures the app as a `FastApiAssistantService` (implementing its required ABC methods), the implemented methods forwards method calls to the provided `FastAPIAssistantService`.

## Assistant service development: general steps

- Set up your dev environment
  - Create a dir for your stuff
  - Create a project there
  - copy dev env skeleton files: .black.toml, Dockerfile, .gitignore, .flake8, Makefile, pyproject.toml which has all of the above files, ready to go.
  - Update README.md
- Getting started with the assistant service
  - copy skeleton of project: e.g. a node engine assistant
  - Consider using the canonical assistant as a starting point,
  - or... copy node_engine scaffolding (make sure to create **init**.py files and a service.py file)
  - Set up .env
- Build and Launch assistant. Run workbench service. Run workbench app. Add assistant local url to workbench via UI.
