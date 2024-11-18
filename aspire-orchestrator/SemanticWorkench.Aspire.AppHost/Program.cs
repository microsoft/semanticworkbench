var builder = DistributedApplication.CreateBuilder(args);

var workbenchService = builder.AddWorkbenchService("workbenchservice",
                                            projectDirectory: Path.Combine("..", "..", "workbench-service"));
var workbenchServiceEndpoint = workbenchService.GetSemanticWorkbenchEndpoint(builder.ExecutionContext.IsPublishMode);

var dotnetAgent3 = builder.AddProject<Projects.dotnet_03_simple_chatbot>("agent3")
    .WithReference(workbenchServiceEndpoint)
    .WaitFor(workbenchService);
dotnetAgent3.WithReference(dotnetAgent3);

builder.AddAssistantApp("skill-assistant",
                        projectDirectory: Path.Combine("..", "..", "assistants", "skill-assistant"),
                        assistantModuleName: "skill-assistant")
    .WithEnvironment(name: "assistant__workbench_service_url", workbenchServiceEndpoint);

var workbenchapp = builder.AddViteApp("workbenchapp", workingDirectory: Path.Combine("..", "..", "workbench-app"), packageManager: "pnpm")
    .WithPnpmPackageInstallation()
    .WithEnvironment(name: "VITE_SEMANTIC_WORKBENCH_SERVICE_URL", workbenchServiceEndpoint)
    .WaitFor(workbenchService)
    .PublishAsDockerFile();

if(!builder.ExecutionContext.IsPublishMode)
{
    workbenchapp.WithHttpsEndpoint(env: "PORT");
}

builder.Build().Run();