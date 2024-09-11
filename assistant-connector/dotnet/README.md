# Semantic Workbench

Semantic Workbench is a versatile tool designed for quickly prototyping intelligent assistants.
Whether you're building new assistants or integrating existing ones, the workbench offers a unified
interface for managing conversations, configuring settings, and customizing behavior.

# Connector

The Connector allows to seamlessly integrate .NET agents, built with any framework, into Semantic
Workbench. By using HTTP for communication, the connector enables your agent to handle instructions
and exchange data with both the frontend and backend of Semantic Workbench.

# Setup Guide

To integrate your agent:

1. Add the `Microsoft.SemanticWorkbench.Connector` nuget to the .NET project containing your agent.

2. **Define an agent configuration**: Create a configuration class for your agent. This can be empty
   if no configuration is needed from the workbench UI.

3. **Extend Agent Functionality**: Inherit from `Microsoft.SemanticWorkbench.Connector.AgentBase`
   and implement the `GetDefaultConfig` and `ParseConfig` methods in your agent class. Examples
   are available in the repository.

4. **Create a Connector**: Implement `Microsoft.SemanticWorkbench.Connector.WorkbenchConnector` and
   its `CreateAgentAsync` method to allow the workbench to create multiple agent instances.

5. Start a `Microsoft.SemanticWorkbench.Connector.WorkbenchConnector` calling the `ConnectAsync`
   method.

6. Start a Web service using the endpoints defined in `Microsoft.SemanticWorkbench.Connector.Webservice`.

# Examples

Find sample .NET agents and assistants using this connector in the
[official repository](https://github.com/microsoft/semanticworkbench/tree/main/examples).
