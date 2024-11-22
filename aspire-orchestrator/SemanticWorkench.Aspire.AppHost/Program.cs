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
    .PublishAsDockerFile([new DockerBuildArg("VITE_SEMANTIC_WORKBENCH_CLIENT_ID", Environment.GetEnvironmentVariable("EntraId__ClientId")),
        new DockerBuildArg("VITE_SEMANTIC_WORKBENCH_AUTHORITY", Environment.GetEnvironmentVariable("EntraId__Authority")),
        new DockerBuildArg("SSHD_ENABLED", "false")]);

// Sample Python agent
builder.AddAssistantApp("skill-assistant", projectDirectory: Path.Combine("..", "..", "assistants", "skill-assistant"), assistantModuleName: "skill-assistant")
    .WithEnvironment(name: "assistant__workbench_service_url", workbenchServiceEndpoint);

// Sample .NET agent
var dotnetAgent3 = builder.AddProject<Projects.dotnet_03_simple_chatbot>("agent3")
    .WithReference(workbenchServiceEndpoint)
    .WaitFor(workbenchService);
// the agent needs to reference its own endpoint in order to send it to the workbench service when it registers
dotnetAgent3.WithEnvironment("Workbench__ConnectorEndpoint", $"{dotnetAgent3.GetEndpoint("http")}/myagents")
    .WithEnvironment("Workbench__WorkbenchEndpoint", workbenchServiceEndpoint);

if (!builder.ExecutionContext.IsPublishMode)
{
    workbenchApp.WithHttpsEndpoint(env: "PORT");
}

builder.Build().Run();