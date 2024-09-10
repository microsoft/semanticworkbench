// Copyright (c) Microsoft. All rights reserved.

using Azure;
using Azure.AI.ContentSafety;
using Azure.Identity;
using Microsoft.SemanticWorkbench.Connector;

namespace AgentExample;

internal static class Program
{
    private const string CORSPolicyName = "MY-CORS";

    internal static async Task Main(string[] args)
    {
        // Setup
        WebApplicationBuilder appBuilder = WebApplication.CreateBuilder(args);

        // Load settings from files and env vars
        appBuilder.Configuration
            .AddJsonFile("appsettings.json")
            .AddJsonFile("appsettings.Development.json", optional: true)
            .AddJsonFile("appsettings.development.json", optional: true)
            .AddEnvironmentVariables();

        // Storage layer to persist agents configuration and conversations
        appBuilder.Services.AddSingleton<IAgentServiceStorage, AgentServiceStorage>();

        // Agent service to support multiple agent instances
        appBuilder.Services.AddSingleton<WorkbenchConnector, MyWorkbenchConnector>();

        // Azure AI Content Safety, used to monitor I/O
        appBuilder.Services.AddAzureAIContentSafety(appBuilder.Configuration.GetSection("AzureContentSafety"));

        // Misc
        appBuilder.Services.AddLogging()
            .AddCors(opt => opt.AddPolicy(CORSPolicyName, pol => pol.WithMethods("GET", "POST", "PUT", "DELETE")));

        // Build
        WebApplication app = appBuilder.Build();
        app.UseCors(CORSPolicyName);

        // Connect to workbench backend, keep alive, and accept incoming requests
        var connectorEndpoint = app.Configuration.GetSection("Workbench").Get<WorkbenchConfig>()!.ConnectorEndpoint;
        using var agentService = app.UseAgentWebservice(connectorEndpoint, true);
        await agentService.ConnectAsync().ConfigureAwait(false);

        // Start app and webservice
        await app.RunAsync().ConfigureAwait(false);
    }

    private static IServiceCollection AddAzureAIContentSafety(
        this IServiceCollection services,
        IConfiguration config)
    {
        var authType = config.GetValue<string>("AuthType");
        var endpoint = config.GetValue<string>("Endpoint");
        var apiKey = config.GetValue<string>("ApiKey");

        return services.AddSingleton<ContentSafetyClient>(_ => authType == "AzureIdentity"
            ? new ContentSafetyClient(new Uri(endpoint!), new DefaultAzureCredential())
            : new ContentSafetyClient(new Uri(endpoint!),
                new AzureKeyCredential(apiKey!)));
    }
}
