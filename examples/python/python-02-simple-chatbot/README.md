# Using Semantic Workbench with python assistants

This project provides a functional chatbot example, leveraging OpenAI or Azure OpenAI (or any OpenAI compatible service),
allowing to use **Semantic Workbench** to test it.

## Responsible AI

The chatbot includes some important best practices for AI development, such as:

- **System prompt safety**, ie a set of LLM guardrails to protect users. As a developer you should understand how these
  guardrails work in your scenarios, and how to change them if needed. The system prompt and the prompt safety
  guardrails are split in two to help with testing. When talking to LLM models, prompt safety is injected before the
  system prompt.
  - See https://learn.microsoft.com/azure/ai-services/openai/concepts/system-message for more details
    about protecting application and users in different scenarios.
- **Content moderation**, via [Azure AI Content Safety](https://azure.microsoft.com/products/ai-services/ai-content-safety)
  or [OpenAI Content Moderation](https://platform.openai.com/docs/guides/moderation).

See the [Responsible AI FAQ](../../../RESPONSIBLE_AI_FAQ.md) for more information.

## Suggested Development Environment

- Use GitHub Codespaces for a quick, turn-key dev environment: [.devcontainer/README.md](../../../.devcontainer/README.md)
- VS Code is recommended for development

## Pre-requisites

- Set up your dev environment
  - SUGGESTED: Use GitHub Codespaces for a quick, easy, and consistent dev
    environment: [.devcontainer/README.md](../../../.devcontainer/README.md)
  - ALTERNATIVE: Local setup following the [main README](../../../README.md#quick-start---local-development-environment)
- Set up and verify that the workbench app and service are running using the [semantic-workbench.code-workspace](../../../semantic-workbench.code-workspace)
- If using Azure OpenAI, set up an Azure account and create a Content Safety resource
  - See [Azure AI Content Safety](https://azure.microsoft.com/products/ai-services/ai-content-safety) for more information
  - Copy the `.env.example` to `.env` and update the `ASSISTANT__AZURE_CONTENT_SAFETY_ENDPOINT` value with the endpoint of your Azure Content Safety resource
  - From VS Code > `Terminal`, run `az login` to authenticate with Azure prior to starting the assistant

## Steps

- Use VS Code > `Run and Debug` (ctrl/cmd+shift+d) > `semantic-workbench` to start the app and service from this workspace
- Use VS Code > `Run and Debug` (ctrl/cmd+shift+d) > `launch assistant` to start the assistant.
- If running in a devcontainer, follow the instructions in [.devcontainer/POST_SETUP_README.md](../../../.devcontainer/POST_SETUP_README.md#start-the-app-and-service) for any additional steps.
- Return to the workbench app to interact with the assistant
- Add a new assistant from the main menu of the app, choose the assistant name as defined by the `service_name` in [chat.py](./assistant/chat.py)
- Click the newly created assistant to configure and interact with it

## Starting the example from CLI

If you're not using VS Code and/or Codespaces, you can also work from the
command line, using `uv`:

```
cd <PATH TO THIS FOLDER>

uv sync

uv run start-semantic-workbench-assistant assistant.chat:app
```

## Create your own assistant

Copy the contents of this folder to your project.

- The paths are already set if you put in the same repo root and relative path of `/<your_projects>/<your_assistant_name>`
- If placed in a different location, update the references in the `pyproject.toml` to point to the appropriate locations for the `semantic-workbench-*` packages

## From Development to Production

It's important to highlight how Semantic Workbench is a development tool, and it's not designed to host agents in
a production environment. The workbench helps with testing and debugging, in a development and isolated environment, usually your localhost.

The core of your assistant/AI application, e.g. how it reacts to users, how it invokes tools, how it stores data, can be
developed with any framework, such as Semantic Kernel, Langchain, OpenAI assistants, etc. That is typically the code
you will add to `chat.py`.

**Semantic Workbench is not a framework**. Dependencies on `semantic-workbench-assistant` package are used only to test and debug your code in Semantic Workbench. **When an assistant is fully developed and ready for production, configurable settings should be hard coded, dependencies on `semantic-workbench-assistant` and similar should be removed**.
