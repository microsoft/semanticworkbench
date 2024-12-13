// Copyright (c) Microsoft. All rights reserved.

using Aspire.Hosting.Extensions;
using Projects;

internal static class Program
{
    public static void Main(string[] args)
    {
        var builder = DistributedApplication.CreateBuilder(args);

        builder
            .AddSemanticWorkbench(out IResourceBuilder<ExecutableResource> workbenchBackend, out EndpointReference workbenchEndpoint)
            .AddPythonAssistant("skill-assistant", workbenchEndpoint)
            .AddDotnetExample<dotnet_03_simple_chatbot>("simple-chatbot-dotnet", workbenchBackend, workbenchEndpoint);

        // When running locally
        if (!builder.ExecutionContext.IsPublishMode)
        {
            builder
                .AddPythonExample("python-01-echo-bot", workbenchEndpoint)
                .AddPythonExample("python-02-simple-chatbot", workbenchEndpoint)
                .AddPythonExample("python-03-multimodel-chatbot", workbenchEndpoint)
                .AddPythonAssistant("explorer-assistant", workbenchEndpoint)
                .AddPythonAssistant("guided-conversation-assistant", workbenchEndpoint)
                .AddPythonAssistant("prospector-assistant", workbenchEndpoint)
                .AddDotnetExample<dotnet_01_echo_bot>("echo-bot-dotnet", workbenchBackend, workbenchEndpoint)
                .AddDotnetExample<dotnet_02_message_types_demo>("sw-tutorial-bot-dotnet", workbenchBackend, workbenchEndpoint);
        }

        builder
            .ShowDashboardUrl(true)
            .LaunchDashboard(delay: 5000)
            .Build()
            .Run();
    }

    /// <summary>
    /// Add the workbench frontend and backend components
    /// </summary>
    private static IDistributedApplicationBuilder AddSemanticWorkbench(this IDistributedApplicationBuilder builder,
        out IResourceBuilder<ExecutableResource> workbenchBackend, out EndpointReference workbenchServiceEndpoint)
    {
        var authority = builder.AddParameterFromConfiguration("authority", "EntraId:Authority");
        var clientId = builder.AddParameterFromConfiguration("clientId", "EntraId:ClientId");

        // Workbench backend
        workbenchBackend = builder.AddWorkbenchService(
            name: "workbenchservice",
            projectDirectory: Path.Combine("..", "..", "workbench-service"),
            clientId: clientId);

        workbenchServiceEndpoint = workbenchBackend.GetSemanticWorkbenchEndpoint(builder.ExecutionContext.IsPublishMode);

        // Workbench frontend
        var workbenchApp = builder.AddViteApp(
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

        // When running locally
        if (!builder.ExecutionContext.IsPublishMode)
        {
            if (!int.TryParse(builder.Configuration["Workbench:AppPort"], out var appPort)) { appPort = 4000; }
            workbenchApp.WithHttpsEndpoint(port: appPort, env: "PORT", isProxied: false);
        }

        return builder;
    }

    private static IDistributedApplicationBuilder AddPythonAssistant(this IDistributedApplicationBuilder builder,
        string name, EndpointReference workbenchServiceEndpoint)
    {
        builder
            .AddAssistantUvPythonApp(
                name: name,
                projectDirectory: Path.Combine("..", "..", "assistants", name),
                assistantModuleName: name)
            .WithEnvironment(name: "assistant__workbench_service_url", workbenchServiceEndpoint);

        return builder;
    }

    private static IDistributedApplicationBuilder AddPythonExample(this IDistributedApplicationBuilder builder,
        string name, EndpointReference workbenchServiceEndpoint)
    {
        builder
            .AddAssistantUvPythonApp(
                name: name,
                projectDirectory: Path.Combine("..", "..", "examples", "python", name),
                assistantModuleName: "assistant")
            .WithEnvironment(name: "assistant__workbench_service_url", workbenchServiceEndpoint);

        return builder;
    }

    // .NET Agent Example 1
    private static IDistributedApplicationBuilder AddDotnetExample<T>(this IDistributedApplicationBuilder builder,
        string name, IResourceBuilder<ExecutableResource> workbenchBackend, EndpointReference workbenchServiceEndpoint) where T : IProjectMetadata, new()
    {
        var agent = builder
            .AddProject<T>(name: name)
            .WithHttpEndpoint()
            .WaitFor(workbenchBackend)
            .WithEnvironment(name: "Workbench__WorkbenchEndpoint", workbenchServiceEndpoint);

        agent.WithEnvironment("Workbench__ConnectorHost", $"{agent.GetEndpoint("http")}");

        return builder;
    }
}
