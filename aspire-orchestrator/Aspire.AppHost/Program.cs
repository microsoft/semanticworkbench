// Copyright (c) Microsoft. All rights reserved.

var builder = DistributedApplication.CreateBuilder(args);

var authority = builder.AddParameterFromConfiguration("authority", "EntraId:Authority");
var clientId = builder.AddParameterFromConfiguration("clientId", "EntraId:ClientId");

// Workbench backend
var workbenchService = builder.AddWorkbenchService("workbenchservice", projectDirectory: Path.Combine("..", "..", "workbench-service"), clientId: clientId);
var workbenchServiceEndpoint = workbenchService.GetSemanticWorkbenchEndpoint(builder.ExecutionContext.IsPublishMode);

// Workbench frontend
var workbenchApp = builder.AddViteApp("workbenchapp", workingDirectory: Path.Combine("..", "..", "workbench-app"), packageManager: "pnpm")
    .WithPnpmPackageInstallation()
    .WithEnvironment(name: "VITE_SEMANTIC_WORKBENCH_SERVICE_URL", workbenchServiceEndpoint)
    .WaitFor(workbenchService)
    .PublishAsDockerFile([
        new DockerBuildArg("VITE_SEMANTIC_WORKBENCH_CLIENT_ID", clientId.Resource.Value),
        new DockerBuildArg("VITE_SEMANTIC_WORKBENCH_AUTHORITY", authority.Resource.Value),
        new DockerBuildArg("SSHD_ENABLED", "false")
    ]);

// Sample Python agent
builder.AddAssistantApp("skill-assistant", projectDirectory: Path.Combine("..", "..", "assistants", "skill-assistant"), assistantModuleName: "skill-assistant")
    .WithEnvironment(name: "assistant__workbench_service_url", workbenchServiceEndpoint);

// Sample .NET agent
var simpleChatBot = builder.AddProject<Projects.dotnet_03_simple_chatbot>("simple-chatbot-dotnet")
    .WaitFor(workbenchService)
    .WithEnvironment(name: "Workbench__WorkbenchEndpoint", workbenchServiceEndpoint);

simpleChatBot.WithEnvironment("Workbench__ConnectorHost", $"{simpleChatBot.GetEndpoint("http")}");

if (!builder.ExecutionContext.IsPublishMode)
{
    workbenchApp.WithHttpsEndpoint(env: "PORT");
}

builder.Build().Run();
