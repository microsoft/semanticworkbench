// Copyright (c) Microsoft. All rights reserved.

namespace Aspire.Hosting;

public static class WorkbenchServiceHostingExtensions
{
    public static IResourceBuilder<ExecutableResource> AddWorkbenchService(
        this IDistributedApplicationBuilder builder,
        string name,
        string projectDirectory,
        IResourceBuilder<ParameterResource> clientId,
        params string[] scriptArgs)
    {
        ArgumentNullException.ThrowIfNull(builder);

        var workbenchService = builder
            .AddUvApp(name, projectDirectory, "start-semantic-workbench-service", scriptArgs)
            .PublishAsDockerImage(dockerContext: Path.Combine("..", ".."),
                dockerFilePath: Path.Combine("workbench-service", "Dockerfile"),
                configure: new(configure => configure
                    .WithBuildArg("SSHD_ENABLED", "false")))
            .WithEnvironment(name: "WORKBENCH__AUTH__ALLOWED_APP_ID", clientId.Resource.Value);

        if (builder.ExecutionContext.IsPublishMode)
        {
            // When running on Azure
            workbenchService.WithHttpsEndpoint(port: 3000);
        }
        else
        {
            // When running locally
            workbenchService.WithHttpEndpoint(env: "PORT");
        }

        workbenchService.WithExternalHttpEndpoints();

        return workbenchService;
    }

    public static EndpointReference GetSemanticWorkbenchEndpoint(this IResourceBuilder<ExecutableResource> workbenchService, bool isPublishMode)
    {
        ArgumentNullException.ThrowIfNull(workbenchService);

        return workbenchService.GetEndpoint(isPublishMode ? "https" : "http");
    }

    public static IResourceBuilder<ExecutableResource> AddAssistantUvPythonApp(
        this IDistributedApplicationBuilder builder,
        string name,
        string projectDirectory,
        string assistantModuleName)
    {
        ArgumentNullException.ThrowIfNull(builder);

        var assistant = builder
            .AddUvApp(name, projectDirectory, "start-assistant")
            .PublishAsDockerImage(dockerContext: Path.Combine("..", ".."),
                dockerFilePath: Path.Combine("tools", "docker", "Dockerfile.assistant"),
                configure: new(configure => configure
                    .WithBuildArg("package", assistantModuleName)
                    .WithBuildArg("app", $"assistant.{assistantModuleName.Replace('-', '_')}:app")
                ));

        if (builder.ExecutionContext.IsPublishMode)
        {
            // When running on Azure
            assistant.WithHttpEndpoint(port: 3001, env: "ASSISTANT__PORT");
        }
        else
        {
            // When running locally
            assistant.WithHttpEndpoint(env: "ASSISTANT__PORT");
        }

        var assistantEndpoint = assistant.GetEndpoint("http");
        assistant.WithEnvironment(name: "assistant__assistant_service_url", assistantEndpoint);

        return assistant;
    }
}
