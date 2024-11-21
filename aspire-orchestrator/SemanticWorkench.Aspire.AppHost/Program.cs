// Copyright (c) Microsoft. All rights reserved.

var builder = DistributedApplication.CreateBuilder(args);

// Workbench backend
var workbenchService = builder.AddWorkbenchService("workbenchservice", projectDirectory: Path.Combine("..", "..", "workbench-service"));
var workbenchServiceEndpoint = workbenchService.GetSemanticWorkbenchEndpoint(builder.ExecutionContext.IsPublishMode);

// Workbench frontend
var workbenchApp = builder.AddViteApp("workbenchapp", workingDirectory: Path.Combine("..", "..", "workbench-app"), packageManager: "pnpm")
    .WithPnpmPackageInstallation()
    .WithEnvironment(name: "VITE_SEMANTIC_WORKBENCH_SERVICE_URL", workbenchServiceEndpoint)
    .WaitFor(workbenchService)
    .PublishAsDockerFile([new DockerBuildArg("VITE_SEMANTIC_WORKBENCH_SERVICE_URL", workbenchServiceEndpoint)]);

// Sample Python agent
builder.AddAssistantApp("skill-assistant", projectDirectory: Path.Combine("..", "..", "assistants", "skill-assistant"), assistantModuleName: "skill-assistant")
    .WithEnvironment(name: "assistant__workbench_service_url", workbenchServiceEndpoint);

// Sample .NET agent
var dotnetAgent3 = builder.AddProject<Projects.dotnet_03_simple_chatbot>("agent3")
    .WithReference(workbenchServiceEndpoint)
    .WaitFor(workbenchService);
dotnetAgent3.WithReference(dotnetAgent3);

if (!builder.ExecutionContext.IsPublishMode)
{
    workbenchApp.WithHttpsEndpoint(env: "PORT");
}

builder.Build().Run();