using CommunityToolkit.Aspire.Hosting.Uvicorn;
using Microsoft.Extensions.Hosting;

var builder = DistributedApplication.CreateBuilder(args);

EndpointReference workbenchServiceEndpoint;
var workbenchService = builder.AddUvicornApp("workbenchservice",
                                            projectDirectory: Path.Combine("..", "..", "workbench-service"),
                                            scriptPath: "start-semantic-workbench-service")
    .PublishAsDockerImage(dockerContext: Path.Combine("..", ".."), dockerFilePath: Path.Combine("workbench-service", "Dockerfile"));
if (builder.ExecutionContext.IsPublishMode)
{
    workbenchService.WithHttpsEndpoint(port: 3000);
    workbenchServiceEndpoint = workbenchService.GetEndpoint("https");
} else
{
    workbenchService.WithHttpEndpoint(env: "PORT");
    workbenchServiceEndpoint = workbenchService.GetEndpoint("http");
}
workbenchService.WithExternalHttpEndpoints();

var dotnetAgent3 = builder.AddProject<Projects.dotnet_03_simple_chatbot>("agent3")
    .WithReference(workbenchServiceEndpoint)
    .WaitFor(workbenchService);
dotnetAgent3.WithReference(dotnetAgent3);

var skillAssistant = builder.AddUvicornApp("skill-assistant",
                                        projectDirectory: Path.Combine("..", "..", "assistants", "skill-assistant"),
                                        scriptPath: "start-semantic-workbench-assistant",
                                        scriptArgs: ["assistant.skill_assistant:app"])
    .WithEnvironment(name: "assistant__workbench_service_url", workbenchServiceEndpoint)
    .PublishAsDockerImage(dockerContext: Path.Combine("..", ".."),
        dockerFilePath: Path.Combine("tools", "docker", "Dockerfile.assistant"),
        configure: new (configure => configure
            .WithBuildArg("package", "skill-assistant")
            .WithBuildArg("app", "assistant.skill_assistant:app")
        ));
if(builder.ExecutionContext.IsPublishMode)
{
    skillAssistant.WithHttpEndpoint(port: 3001, env: "ASSISTANT__PORT");
} else
{
    skillAssistant.WithHttpEndpoint(env: "ASSISTANT__PORT");
}
var skillAssistantEndpoint = skillAssistant.GetEndpoint("http");
skillAssistant.WithEnvironment(name: "assistant__assistant_service_url", skillAssistantEndpoint);

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