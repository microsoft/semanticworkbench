# Semantic Workbench Assistant Development Guide

## Overview

For assistants to be instantiated in Semantic Workbench, you need to implement an assistant service that the workbench can talk with via http.

We provide several python base classes to make this easier: [semantic-workbench-assistant](../semantic-workbench/v1/service/semantic-workbench-assistant/README.md)

Example assistant services:

- [Canonical assistant example](../semantic-workbench/v1/service/semantic-workbench-assistant/semantic_workbench_assistant/canonical.py)
- Python assistant [example 1](../examples/python-example01/README.md)
- .NET agent [example 1](../examples/dotnet-example01/README.md) and [example 2](../examples/dotnet-example02/README.md)

## Top level concepts

RECOMMENDED FOR PYTHON: Use the `semantic-workbench-assistant` base classes to create your assistant service. These classes provide a lot of the boilerplate code for you.

See the [semantic-workbench-assistant.assistant_base](../service/semantic-workbench-assistant/semantic_workbench_assistant/assistant_base.py) for the base classes
and the Python [example 1](../examples/python-example01/README.md) for an example of how to use them.

### assistant_service.FastAPIAssistantService

Your main job is to implement a service that supports all the Semantic Workbench methods. The [Canonical assistant example](../semantic-workbench/v1/service/semantic-workbench-assistant/semantic_workbench_assistant/canonical.py) demonstrates a minimal implementation.

It implements an assistant service that inherits from FastAPIAssistantService:

`class CanonicalAssistant(assistant_service.FastAPIAssistantService):`

This service is now a FastAPIAssistantService containing all the assistant methods that can be overridden as desired.

## Assistant service development: general steps

- Set up your dev environment
  - SUGGESTED: Use GitHub Codespaces for a quick, easy, and consistent dev
    environment: [/.devcontainer/README.md](../.devcontainer/README.md)
  - ALTERNATIVE: Local setup following the [main README](../README.md#quick-start---local-development-environment)
- Create a dir for your projects. If you create this in the repo root, any assistant example projects will already have the correct relative paths set up to access the `semantic-workbench-*` packages or libraries.
- Create a project for your new assistant in your projects dir, e.g. `/<your_projects>/<your_assistant_name>`
- Getting started with the assistant service
  - Copy skeleton of an existing project: e.g. one of the projects from the [examples](../examples) directory
    - Alternatively, consider using the canonical assistant as a starting point if you want to implement a new custom base
  - Set up .env
- Build and Launch assistant. Run workbench service. Run workbench app. Add assistant local url to workbench via UI.
- NOTE: See additional documentation in [/semantic-workbench/v1/app/docs](../semantic-workbench/v1/app/docs/) regarding app features that can be used in the assistant service.

## Assistant service deployment

DISCLAIMER: The security considerations of hosting a service with a public endpoint are beyond the scope of this document. Please ensure you understand the implications of hosting a service before doing so. It is not recommended to host a publicly available instance of the Semantic Workbench app.

If you want to deploy your assistant service to a public endpoint, you will need to create your own Azure app registration and update the app and service files with the new app registration details. See the [Custom app registration](../docs/CUSTOM_APP_REGISTRATION.md) guide for more information.

### Steps

TODO: Add more detailed steps, this is a high-level overview

- Create a new Azure app registration
- Update your app and service files with the new app registration details
- Deploy your service to a public endpoint
- Update the workbench app with the new service URL
- Deploy your assistant service to an endpoint that the workbench service can access
  - Suggested: limit access to the assistant service to only the workbench service using a private network or other security measures)
- Deploy the workbench app to an endpoint that users can access
  - Suggested: limit access to the workbench app to only trusted users
