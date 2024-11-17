using CommunityToolkit.Aspire.Hosting.Uvicorn;
using Microsoft.Extensions.Hosting;

var builder = DistributedApplication.CreateBuilder(args);


var workbenchService = builder.AddUvicornApp("workbenchservice",
                                            projectDirectory: Path.Combine("..", "..", "workbench-service"),
                                            scriptPath: "start-semantic-workbench-service");
if (builder.ExecutionContext.IsPublishMode)
{
    workbenchService.WithHttpEndpoint(port: 3000);
} else
{
    workbenchService.WithHttpEndpoint(env: "PORT");
}
workbenchService.WithExternalHttpEndpoints()
    .PublishAsDockerImage(dockerContext: Path.Combine("..", ".."), dockerFilePath: Path.Combine("workbench-service", "Dockerfile"));
var workbenchServiceEndpoint = workbenchService.GetEndpoint("http");

var dotnetAgent3 = builder.AddProject<Projects.dotnet_03_simple_chatbot>("agent3")
    .WithReference(workbenchServiceEndpoint)
    .WaitFor(workbenchService);
dotnetAgent3.WithReference(dotnetAgent3);

// if (!builder.ExecutionContext.IsPublishMode)
// {
//     var pythonAgent1 = builder.AddUvicornApp("pythonAgent",
//                                             projectDirectory: Path.Combine("..", "..", "examples", "python", "python-01-echo-bot"),
//                                             scriptPath: "start-semantic-workbench-assistant",
//                                             scriptArgs: ["assistant.chat:app"])
//         .WithHttpEndpoint(env: "ASSISTANT__PORT")
//         .WithEnvironment(name: "assistant__workbench_service_url", workbenchServiceEndpoint);
// }

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