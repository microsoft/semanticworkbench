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
        var appBuilder = WebApplication.CreateBuilder(args);

        // Load settings from files and env vars
        appBuilder.Configuration
            .AddJsonFile("appsettings.json")
            .AddJsonFile("appsettings.Development.json", optional: true)
            .AddJsonFile("appsettings.development.json", optional: true)
            .AddEnvironmentVariables();

        appBuilder.Services
            .AddLogging()
            .AddCors(opt => opt.AddPolicy(CORSPolicyName, pol => pol.WithMethods("GET", "POST", "PUT", "DELETE")))
            .AddSingleton<IAgentServiceStorage, AgentServiceStorage>() // Agents storage layer for config and chats
            .AddSingleton<WorkbenchConnector, MyWorkbenchConnector>() // Workbench backend connector
            .AddAzureAIContentSafety(appBuilder.Configuration.GetSection("AzureContentSafety")); // Content moderation

        // Build
        WebApplication app = appBuilder.Build();
        app.UseCors(CORSPolicyName);

        // Connect to workbench backend, keep alive, and accept incoming requests
        var connectorEndpoint = app.Configuration.GetSection("Workbench").Get<WorkbenchConfig>()!.ConnectorEndpoint;
        if(Environment.GetEnvironmentVariable("services__agent3__http__0") != null)
        {
            connectorEndpoint = $"{Environment.GetEnvironmentVariable("services__agent3__http__0")}/myagents";
        }
        Console.WriteLine($"The env var value is {Environment.GetEnvironmentVariable("services__agent3__http__0")}");
        Console.WriteLine($"The connector endpoint is {connectorEndpoint}");
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
        var endpoint = new Uri(config.GetValue<string>("Endpoint")!);
        var apiKey = config.GetValue<string>("ApiKey");

        return services.AddSingleton<ContentSafetyClient>(_ => authType == "AzureIdentity"
            ? new ContentSafetyClient(endpoint, new DefaultAzureCredential())
            : new ContentSafetyClient(endpoint, new AzureKeyCredential(apiKey!)));
    }

    /*
       The Agent in this example allows to switch model, so SK kernel and chat
       service are created at runtime. See MyAgent.GetChatCompletionService().

       When you deploy your agent to Prod you will likely use a single model,
       so you could pass the SK kernel via DI, using the code below.

       Note: Semantic Kernel doesn't allow to use a single chat completion service
             with multiple models. If you use different models, SK expects to define
             multiple services, with a different ID.

    private static IServiceCollection AddSemanticKernel(
        this IServiceCollection services,
        IConfiguration openaiCfg,
        IConfiguration azureAiCfg)
    {
        var openaiEndpoint = openaiCfg.GetValue<string>("Endpoint")
                             ?? throw new ArgumentNullException("OpenAI config not found");

        var openaiKey = openaiCfg.GetValue<string>("ApiKey")
                        ?? throw new ArgumentNullException("OpenAI config not found");

        var azEndpoint = azureAiCfg.GetValue<string>("Endpoint")
                         ?? throw new ArgumentNullException("Azure OpenAI config not found");

        var azAuthType = azureAiCfg.GetValue<string>("AuthType")
                         ?? throw new ArgumentNullException("Azure OpenAI config not found");

        var azApiKey = azureAiCfg.GetValue<string>("ApiKey")
                       ?? throw new ArgumentNullException("Azure OpenAI config not found");

        return services.AddSingleton<Kernel>(_ =>
        {
            var b = Kernel.CreateBuilder();
            b.AddOpenAIChatCompletion(
                modelId: "... model name ...",
                endpoint: new Uri(openaiEndpoint),
                apiKey: openaiKey,
                serviceId: "... service name (e.g. model name) ...");

            if (azAuthType == "AzureIdentity")
            {
                b.AddAzureOpenAIChatCompletion(
                    deploymentName: "... deployment name ...",
                    endpoint: azEndpoint,
                    credentials: new DefaultAzureCredential(),
                    serviceId: "... service name (e.g. model name) ...");
            }
            else
            {
                b.AddAzureOpenAIChatCompletion(
                    deploymentName: "... deployment name ...",
                    endpoint: azEndpoint,
                    apiKey: azApiKey,
                    serviceId: "... service name (e.g. model name) ...");
            }

            return b.Build();
        });
    }
    */
}
