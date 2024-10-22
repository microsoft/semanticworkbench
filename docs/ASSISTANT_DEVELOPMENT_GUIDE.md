# Semantic Workbench Assistant Development Guide

## Overview

For assistants to be instantiated in Semantic Workbench, you need to implement an assistant service that the workbench can talk with via http.

We provide several python base classes to make this easier: [semantic-workbench-assistant](../libraries/python/semantic-workbench-assistant/README.md)

Example assistant services:

- [Canonical assistant example](../libraries/python/semantic-workbench-assistant/semantic_workbench_assistant/canonical.py)
- Python assistant [python-01-echo-bot](../examples/python/python-01-echo-bot/README.md) and [python-02-simple-chatbot](../examples/python/python-02-simple-chatbot/README.md)
- .NET agent [dotnet-01-echo-bot](../examples/dotnet/dotnet-01-echo-bot/README.md), [dotnet-02-message-types-demo](../examples/dotnet/dotnet-02-message-types-demo/README.md) and [dotnet-03-simple-chatbot](../examples/dotnet/dotnet-03-simple-chatbot/README.md)

## Top level concepts

RECOMMENDED FOR PYTHON: Use the `semantic-workbench-assistant` classes to create your assistant service. These classes provide a lot of the boilerplate code for you.

See the [semantic-workbench-assistant.assistant_app.AssistantApp](../libraries/python/semantic-workbench-assistant/semantic_workbench_assistant/assistant_app/assistant.py) for the classes
and the Python [python-01-echo-bot](../examples/python/python-01-echo-bot/README.md) for an example of how to use them.

### assistant_service.FastAPIAssistantService

Your main job is to implement a service that supports all the Semantic Workbench methods. The [Canonical assistant example](../libraries/python/semantic-workbench-assistant/semantic_workbench_assistant/canonical.py) demonstrates a minimal implementation.

It implements an assistant service that inherits from FastAPIAssistantService:

`class CanonicalAssistant(assistant_service.FastAPIAssistantService):`

This service is now a FastAPIAssistantService containing all the assistant methods that can be overridden as desired.

## Assistant service development: general steps

- Create a fork of this repository by clicking the "Fork" button at the top right of the repository page
- Set up your dev environment
  - SUGGESTED: Use GitHub Codespaces for a quick, easy, and consistent dev
    environment: [/.devcontainer/README.md](../.devcontainer/README.md)
  - ALTERNATIVE: Local setup following the [main README](../README.md#local-development-environment)
- Create a directory for your projects. If you create this in the repo root, any assistant example projects will already have the correct relative paths set up to access the `semantic-workbench-*` packages or libraries.
- Create a project for your new assistant in your projects directory, e.g. `/<your_projects>/<your_assistant_name>`
- Getting started with the assistant service
  - Copy skeleton of an existing project: e.g. one of the projects from the [examples](../examples) directory
    - Alternatively, consider using the canonical assistant as a starting point if you want to implement a new custom base
  - Follow the `README.md` in the example project to get started
  - If the project has a `.env.example` file, copy it to `.env` and update the values as needed
- Build and Launch assistant. Run workbench service. Run workbench app. Add assistant local url to workbench via UI.
- NOTE: See additional documentation in [/workbench-app/docs](../workbench-app/docs/) regarding app features that can be used in the assistant service.

## Assistant service deployment

DISCLAIMER: The security considerations of hosting a service with a public endpoint are beyond the scope of this document. Please ensure you understand the implications of hosting a service before doing so. It is not recommended to host a publicly available instance of the Semantic Workbench app.

If you want to deploy your assistant service to a public endpoint, you will need to create your own Azure app registration and update the app and service files with the new app registration details. See the [Custom app registration](../docs/CUSTOM_APP_REGISTRATION.md) guide for more information.

### Deployment steps

_TODO: Add more detailed steps, this is a high-level overview_

- Create a new Azure app registration
- Update your app and service files with the new app registration details
- Deploy your service to an endpoint accessible by your web browser
- Update the workbench app with the new service URL
- Deploy your assistant service to an endpoint that the workbench service can access
  - **Suggested**: limit access to the assistant service to only the workbench service using a private network or other security measures
- Deploy the workbench app to an endpoint that users can access
  - **Suggested**: limit access to the workbench app to only trusted users
