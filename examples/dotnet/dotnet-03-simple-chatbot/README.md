# Using Semantic Workbench with .NET Agents

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
- **Content moderation**, via [Azure AI Content Safety](https://azure.microsoft.com/products/ai-services/ai-content-safety).

## Running the example

1. Configure the agent, creating an `appsettings.development.json` to override values in `appsettings.json`:
   - Content Safety:
     - `AzureContentSafety.Endpoint`: endpoint of your [Azure AI Content Safety](https://azure.microsoft.com/products/ai-services/ai-content-safety) service
     - `AzureContentSafety.AuthType`: change it to `AzureIdentity` if you're using managed identities or similar.
     - `AzureContentSafety.ApiKey`: your service API key (when not using managed identities)
   - AI services:
     - `AzureOpenAI.Endpoint`: endpoint of your Azure OpenAI service (if you are using Azure OpenAI)
     - `AzureOpenAI.AuthType`: change it to `AzureIdentity` if you're using managed identities or similar.
     - `AzureOpenAI.ApiKey`: your service API key (when not using managed identities)
     - `OpenAI.Endpoint`: change the value if you're using OpenAI compatible services like LM Studio
     - `OpenAI.ApiKey`: the service credentials
2. Start the agent, e.g. from this folder run `dotnet run`
3. Start the workbench backend, e.g. from root of the repo: `./tools/run-service.sh`. More info in the [README](../../../README.md).
4. Start the workbench frontend, e.g. from root of the repo: `./tools/run-app.sh`. More info in
   the [README](../../../README.md).

## Project Overview

The sample project utilizes the `WorkbenchConnector` library and the `AgentBase` class to connect the agent to Semantic Workbench.

The `MyAgentConfig` class defines some settings you can customize while developing your agent. For instance you can
change the system prompt, test different safety rules, connect to OpenAI, Azure OpenAI or compatible services like
LM Studio, change LLM temperature and nucleus sampling, etc.

The `appsettings.json` file contains workbench settings, credentials and few other details.

## From Development to Production

It's important to highlight how Semantic Workbench is a development tool, and it's not designed to host agents in
a production environment.
The workbench helps with testing and debugging, in a development and isolated environment, usually your localhost.

The core of your agent/AI application, e.g. how it reacts to users, how it invokes tools, how it stores data, can be
developed with any framework, such as Semantic Kernel, Langchain, OpenAI assistants, etc. That is typically the code
you will add to `MyAgent.cs`.

**Semantic Workbench is not a framework**. Settings like `MyAgentConfig.cs` and dependencies on `WorkbenchConnector`
library are used only to test and debug your code in Semantic Workbench. **When an agent is fully developed and ready
for production, configurable settings should be hard coded, dependencies on `WorkbenchConnector` and `AgentBase` should
be removed**.
