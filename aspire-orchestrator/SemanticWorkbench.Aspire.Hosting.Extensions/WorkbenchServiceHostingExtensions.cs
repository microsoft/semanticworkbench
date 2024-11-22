// Copyright (c) Microsoft. All rights reserved.

namespace Aspire.Hosting;

public static class WorkbenchServiceHostingExtensions
{
    public static IResourceBuilder<ExecutableResource> AddWorkbenchService(
        this IDistributedApplicationBuilder builder,
        string name,
        string projectDirectory,
        params string[] scriptArgs)
    {
        ArgumentNullException.ThrowIfNull(builder);

        var workbenchService = builder.AddUvApp(name, projectDirectory, "start-semantic-workbench-service", scriptArgs)
            .PublishAsDockerImage(dockerContext: Path.Combine("..", ".."),
                dockerFilePath: Path.Combine("workbench-service", "Dockerfile"),
                configure: new (configure => configure
                    .WithBuildArg("SSHD_ENABLED", "false")))
            .WithEnvironment(name: "WORKBENCH__AUTH__ALLOWED_APP_ID", Environment.GetEnvironmentVariable("EntraId__ClientId"));
        if (builder.ExecutionContext.IsPublishMode)
        {
            workbenchService.WithHttpsEndpoint(port: 3000);
        } else
        {
            workbenchService.WithHttpEndpoint(env: "PORT");
        }
        workbenchService.WithExternalHttpEndpoints();

        return workbenchService;
    }

    public static EndpointReference GetSemanticWorkbenchEndpoint(this IResourceBuilder<ExecutableResource> workbenchService, bool isPublishMode)
    {
        ArgumentNullException.ThrowIfNull(workbenchService);

        if (isPublishMode)
        {
            return workbenchService.GetEndpoint("https");
        } else
        {
            return workbenchService.GetEndpoint("http");
        }
    }

    public static IResourceBuilder<ExecutableResource> AddAssistantApp(
        this IDistributedApplicationBuilder builder,
        string name,
        string projectDirectory,
        string assistantModuleName)
    {
        ArgumentNullException.ThrowIfNull(builder);

        var assistant = builder.AddUvApp(name, projectDirectory, "start-assistant")
            .PublishAsDockerImage(dockerContext: Path.Combine("..", ".."),
                dockerFilePath: Path.Combine("tools", "docker", "Dockerfile.assistant"),
                configure: new (configure => configure
                    .WithBuildArg("package", assistantModuleName)
                    .WithBuildArg("app", $"assistant.{assistantModuleName.Replace('-', '_')}:app")
                ));
        if(builder.ExecutionContext.IsPublishMode)
        {
            assistant.WithHttpEndpoint(port: 3001, env: "ASSISTANT__PORT");
        } else
        {
            assistant.WithHttpEndpoint(env: "ASSISTANT__PORT");
        }
        var assistantEndpoint = assistant.GetEndpoint("http");
        assistant.WithEnvironment(name: "assistant__assistant_service_url", assistantEndpoint);

        return assistant;
    }
}
