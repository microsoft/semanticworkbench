// Copyright (c) Microsoft. All rights reserved.

var builder = DistributedApplication.CreateBuilder(args);

var authority = builder.AddParameterFromConfiguration("authority", "EntraId:Authority");
var clientId = builder.AddParameterFromConfiguration("clientId", "EntraId:ClientId");

// Workbench backend
var workbenchBackend = AddWorkbenchBackend();
var workbenchEndpoint = workbenchBackend.GetSemanticWorkbenchEndpoint(builder.ExecutionContext.IsPublishMode);

// Workbench frontend
var workbenchApp = AddWorkbenchFrontend(workbenchEndpoint);

switch (builder.ExecutionContext)
{
    // When publishing to Azure
    case { IsPublishMode: true }:
        AddPythonSkillAssistant(workbenchEndpoint);
        AddDotnetAgent3(workbenchEndpoint);
        break;

    // When running locally
    case { IsPublishMode: false }:
        workbenchApp.WithHttpsEndpoint(env: "PORT");

        AddPythonSkillAssistant(workbenchEndpoint);
        // AddPythonMultiModelChatbot(workbenchEndpoint);
        AddDotnetAgent1(workbenchEndpoint);
        AddDotnetAgent2(workbenchEndpoint);
        AddDotnetAgent3(workbenchEndpoint);
        break;
}

builder.Build().Run();

IResourceBuilder<ExecutableResource> AddWorkbenchBackend()
{
    return builder.AddWorkbenchService(
        name: "workbenchservice",
        projectDirectory: Path.Combine("..", "..", "workbench-service"),
        clientId: clientId);
}

IResourceBuilder<NodeAppResource> AddWorkbenchFrontend(EndpointReference workbenchServiceEndpoint)
{
    return builder.AddViteApp(
            name: "workbenchapp",
            workingDirectory: Path.Combine("..", "..", "workbench-app"),
            packageManager: "pnpm")
        .WithPnpmPackageInstallation()
        .WithEnvironment(name: "VITE_SEMANTIC_WORKBENCH_SERVICE_URL", workbenchServiceEndpoint)
        .WaitFor(workbenchBackend)
        .PublishAsDockerFile([
            new DockerBuildArg("VITE_SEMANTIC_WORKBENCH_CLIENT_ID", clientId.Resource.Value),
            new DockerBuildArg("VITE_SEMANTIC_WORKBENCH_AUTHORITY", authority.Resource.Value),
        ]);
}

// .NET Agent Example 1
IResourceBuilder<ProjectResource> AddDotnetAgent1(EndpointReference workbenchServiceEndpoint)
{
    var agent = builder
        .AddProject<Projects.dotnet_01_echo_bot>(name: "echo-bot-dotnet")
        .WithHttpEndpoint()
        .WaitFor(workbenchBackend)
        .WithEnvironment(name: "Workbench__WorkbenchEndpoint", workbenchServiceEndpoint);

    return agent.WithEnvironment("Workbench__ConnectorHost", $"{agent.GetEndpoint("http")}");
}

// .NET Agent Example 2
IResourceBuilder<ProjectResource> AddDotnetAgent2(EndpointReference workbenchServiceEndpoint)
{
    var agent = builder
        .AddProject<Projects.dotnet_02_message_types_demo>(name: "sw-tutorial-bot-dotnet")
        .WithHttpEndpoint()
        .WaitFor(workbenchBackend)
        .WithEnvironment(name: "Workbench__WorkbenchEndpoint", workbenchServiceEndpoint);

    return agent.WithEnvironment("Workbench__ConnectorHost", $"{agent.GetEndpoint("http")}");
}

// .NET Agent Example 3
IResourceBuilder<ProjectResource> AddDotnetAgent3(EndpointReference workbenchServiceEndpoint)
{
    var agent = builder
        .AddProject<Projects.dotnet_03_simple_chatbot>(name: "simple-chatbot-dotnet")
        .WithHttpEndpoint()
        .WaitFor(workbenchBackend)
        .WithEnvironment(name: "Workbench__WorkbenchEndpoint", workbenchServiceEndpoint);

    return agent.WithEnvironment("Workbench__ConnectorHost", $"{agent.GetEndpoint("http")}");
}

// Python Agent example: Skill Assistant
IResourceBuilder<ExecutableResource> AddPythonSkillAssistant(EndpointReference workbenchServiceEndpoint)
{
    return builder
        .AddAssistantApp(
            name: "skill-assistant",
            projectDirectory: Path.Combine("..", "..", "assistants", "skill-assistant"),
            assistantModuleName: "skill-assistant")
        .WithEnvironment(name: "assistant__workbench_service_url", workbenchServiceEndpoint);
}

// Python Agent example: Multi-model chatbot
// IResourceBuilder<ExecutableResource> AddPythonMultiModelChatbot(EndpointReference workbenchServiceEndpoint)
// {
//     return builder
//         .AddAssistantApp(
//             name: "skill-assistant",
//             projectDirectory: Path.Combine("..", "examples", "python", "python-03-multimodel-chatbot"),
//             assistantModuleName: "assistant")
//         .WithEnvironment(name: "assistant__workbench_service_url", workbenchServiceEndpoint);
// }
