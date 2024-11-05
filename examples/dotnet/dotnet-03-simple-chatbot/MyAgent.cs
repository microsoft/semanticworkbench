// Copyright (c) Microsoft. All rights reserved.

using System.Text.Json;
using Azure;
using Azure.AI.ContentSafety;
using Azure.Identity;
using Microsoft.Extensions.Logging.Abstractions;
using Microsoft.SemanticKernel;
using Microsoft.SemanticKernel.ChatCompletion;
using Microsoft.SemanticKernel.Connectors.OpenAI;
using Microsoft.SemanticWorkbench.Connector;

namespace AgentExample;

public class MyAgent : AgentBase<MyAgentConfig>
{
    // Azure Content Safety
    private readonly ContentSafetyClient _contentSafety;

    // .NET app configuration (appsettings.json, appsettings.development.json, env vars)
    private readonly IConfiguration _appConfig;

    /// <summary>
    /// Create a new agent instance
    /// </summary>
    /// <param name="agentId">Agent instance ID</param>
    /// <param name="agentName">Agent name</param>
    /// <param name="agentConfig">Agent configuration</param>
    /// <param name="appConfig">App settings from WebApplication ConfigurationManager</param>
    /// <param name="workbenchConnector">Service containing the agent, used to communicate with Workbench backend</param>
    /// <param name="storage">Agent data storage</param>
    /// <param name="contentSafety">Azure content safety</param>
    /// <param name="loggerFactory">App logger factory</param>
    public MyAgent(
        string agentId,
        string agentName,
        MyAgentConfig? agentConfig,
        IConfiguration appConfig,
        WorkbenchConnector<MyAgentConfig> workbenchConnector,
        IAgentServiceStorage storage,
        ContentSafetyClient contentSafety,
        ILoggerFactory? loggerFactory = null)
        : base(
            workbenchConnector,
            storage,
            loggerFactory?.CreateLogger<MyAgent>() ?? new NullLogger<MyAgent>())
    {
        this._appConfig = appConfig;
        this._contentSafety = contentSafety;

        this.Id = agentId;
        this.Name = agentName;

        // Clone object to avoid config object being shared
        this.Config = JsonSerializer.Deserialize<MyAgentConfig>(JsonSerializer.Serialize(agentConfig)) ?? new MyAgentConfig();
    }

    /// <inheritdoc />
    public override async Task ReceiveCommandAsync(
        string conversationId,
        Command command,
        CancellationToken cancellationToken = default)
    {
        try
        {
            if (!this.Config.CommandsEnabled) { return; }

            // Check if we're replying to other agents
            if (!this.Config.ReplyToAgents && command.Sender.Role == "assistant") { return; }

            // Support only the "say" command
            if (!command.CommandName.Equals("say", StringComparison.OrdinalIgnoreCase)) { return; }

            // Update the chat history to include the message received
            await base.AddMessageToHistoryAsync(conversationId, command, cancellationToken).ConfigureAwait(false);

            // Create the answer content
            var answer = Message.CreateChatMessage(this.Id, command.CommandParams);

            // Update the chat history to include the outgoing message
            this.Log.LogTrace("Store new message");
            await this.AddMessageToHistoryAsync(conversationId, answer, cancellationToken).ConfigureAwait(false);

            // Send the message to workbench backend
            this.Log.LogTrace("Send new message");
            await this.SendTextMessageAsync(conversationId, answer, cancellationToken).ConfigureAwait(false);
        }
        finally
        {
            this.Log.LogTrace("Reset agent status");
            await this.ResetAgentStatusAsync(conversationId, cancellationToken).ConfigureAwait(false);
        }
    }

    /// <inheritdoc />
    public override async Task ReceiveMessageAsync(
        string conversationId,
        Message message,
        CancellationToken cancellationToken = default)
    {
        try
        {
            // Show some status while working...
            await this.SetAgentStatusAsync(conversationId, "Thinking...", cancellationToken).ConfigureAwait(false);

            // Update the chat history to include the message received
            var conversation = await base.AddMessageToHistoryAsync(conversationId, message, cancellationToken).ConfigureAwait(false);

            // Check if we're replying to other agents
            if (!this.Config.ReplyToAgents && message.Sender.Role == "assistant") { return; }

            // Check if max messages count reached
            if (conversation.Messages.Count >= this.Config.MaxMessagesCount)
            {
                var notice = Message.CreateNotice(this.Id, "Max chat length reached.");
                await this.SendTextMessageAsync(conversationId, notice, cancellationToken).ConfigureAwait(false);

                this.Log.LogDebug("Max chat length reached. Length: {0}", conversation.Messages.Count);
                // Stop sending messages to avoid entering a loop
                return;
            }

            // Ignore empty messages
            if (string.IsNullOrWhiteSpace(message.Content))
            {
                this.Log.LogTrace("The message received is empty, nothing to do");
                return;
            }

            Message answer = await this.PrepareAnswerAsync(conversation, message, cancellationToken).ConfigureAwait(false);

            // Update the chat history to include the outgoing message
            this.Log.LogTrace("Store new message");
            conversation = await this.AddMessageToHistoryAsync(conversationId, answer, cancellationToken).ConfigureAwait(false);

            // Send the message to workbench backend
            this.Log.LogTrace("Send new message");
            await this.SendTextMessageAsync(conversationId, answer, cancellationToken).ConfigureAwait(false);

            // Show chat history in workbench side panel
            await this.LogChatHistoryAsInsight(conversation, cancellationToken).ConfigureAwait(false);
        }
        catch (Exception e)
        {
            this.Log.LogError(e, "Something went wrong, unable to reply");
            throw;
        }
        finally
        {
            this.Log.LogTrace("Reset agent status");
            await this.ResetAgentStatusAsync(conversationId, cancellationToken).ConfigureAwait(false);
        }
    }

    #region internals

    private async Task<Message> PrepareAnswerAsync(Conversation conversation, Message message, CancellationToken cancellationToken)
    {
        Message answer;

        try
        {
            var (inputIsSafe, inputSafetyReport) = await this.IsSafeAsync(message.Content, cancellationToken).ConfigureAwait(false);

            var debugInfo = new DebugInfo
            {
                { "replyingTo", message.Content },
                { "inputIsSafe", inputIsSafe },
                { "inputSafetyReport", inputSafetyReport },
            };

            if (inputIsSafe)
            {
                var chatHistory = conversation.ToSemanticKernelChatHistory(this.Id, this.Config.RenderSystemPrompt());
                debugInfo.Add("lastChatMsg", chatHistory.Last().Content);

                // Show chat history in workbench side panel
                await this.LogChatHistoryAsInsight(conversation, cancellationToken).ConfigureAwait(false);

                // Generate answer
                var assistantReply = await this.GenerateAnswerWithLLMAsync(chatHistory, debugInfo, cancellationToken).ConfigureAwait(false);

                // Sanitize answer
                var (outputIsSafe, outputSafetyReport) = await this.IsSafeAsync(assistantReply.Content, cancellationToken).ConfigureAwait(false);

                debugInfo.Add("outputIsSafe", outputIsSafe);
                debugInfo.Add("outputSafetyReport", outputSafetyReport);

                // Check the output too
                if (outputIsSafe)
                {
                    answer = Message.CreateChatMessage(this.Id, assistantReply.Content ?? "", debugInfo);
                }
                else
                {
                    this.Log.LogWarning("The answer generated is not safe");
                    answer = Message.CreateChatMessage(this.Id, "Let's talk about something else.", debugInfo);

                    var note = Message.CreateNote(this.Id, "Malicious output detected", debug: new { outputSafetyReport, assistantReply.Content });
                    await this.SendTextMessageAsync(conversation.Id, note, cancellationToken).ConfigureAwait(false);
                }
            }
            else
            {
                this.Log.LogWarning("The input message is not safe");
                answer = Message.CreateChatMessage(this.Id, "I'm not sure how to respond to that.", inputSafetyReport);

                var note = Message.CreateNote(this.Id, "Malicious input detected", debug: inputSafetyReport);
                await this.SendTextMessageAsync(conversation.Id, note, cancellationToken).ConfigureAwait(false);
            }
        }
#pragma warning disable CA1031
        catch (Exception e)
#pragma warning restore CA1031
        {
            this.Log.LogError(e, "Error while generating message");
            answer = Message.CreateChatMessage(this.Id, $"Sorry, something went wrong: {e.Message}.", debug: new { e.Message, InnerException = e.InnerException?.Message });
        }

        return answer;
    }

    private async Task<ChatMessageContent> GenerateAnswerWithLLMAsync(
        ChatHistory chatHistory,
        DebugInfo debugInfo,
        CancellationToken cancellationToken)
    {
        var llm = this.GetChatCompletionService();
        var aiSettings = new OpenAIPromptExecutionSettings
        {
            ModelId = this.Config.ModelName,
            Temperature = this.Config.Temperature,
            TopP = this.Config.NucleusSampling,
        };

        debugInfo.Add("systemPrompt", this.Config.RenderSystemPrompt());
        debugInfo.Add("modelName", this.Config.ModelName);
        debugInfo.Add("temperature", this.Config.Temperature);
        debugInfo.Add("nucleusSampling", this.Config.NucleusSampling);

        var assistantReply = await llm.GetChatMessageContentAsync(chatHistory, aiSettings, cancellationToken: cancellationToken).ConfigureAwait(false);

        debugInfo.Add("answerMetadata", assistantReply.Metadata);

        return assistantReply;
    }

    /// <summary>
    /// Note: Semantic Kernel doesn't allow to use a chat completion service
    /// with multiple models, so the kernel and the service are created on the fly
    /// rather than injected with DI.
    /// </summary>
    private IChatCompletionService GetChatCompletionService()
    {
        IKernelBuilder b = Kernel.CreateBuilder();

        switch (this.Config.LLMProvider)
        {
            case "openai":
            {
                var c = this._appConfig.GetSection("OpenAI");
                var openaiEndpoint = c.GetValue<string>("Endpoint")
                                     ?? throw new ArgumentNullException("OpenAI config not found");

                var openaiKey = c.GetValue<string>("ApiKey")
                                ?? throw new ArgumentNullException("OpenAI config not found");

                b.AddOpenAIChatCompletion(
                    modelId: this.Config.ModelName,
                    endpoint: new Uri(openaiEndpoint),
                    apiKey: openaiKey,
                    serviceId: this.Config.LLMProvider);
                break;
            }
            case "azure-openai":
            {
                var c = this._appConfig.GetSection("AzureOpenAI");
                var azEndpoint = c.GetValue<string>("Endpoint")
                                 ?? throw new ArgumentNullException("Azure OpenAI config not found");

                var azAuthType = c.GetValue<string>("AuthType")
                                 ?? throw new ArgumentNullException("Azure OpenAI config not found");

                var azApiKey = c.GetValue<string>("ApiKey")
                               ?? throw new ArgumentNullException("Azure OpenAI config not found");

                if (azAuthType == "AzureIdentity")
                {
                    b.AddAzureOpenAIChatCompletion(
                        deploymentName: this.Config.ModelName,
                        endpoint: azEndpoint,
                        credentials: new DefaultAzureCredential(),
                        serviceId: "azure-openai");
                }
                else
                {
                    b.AddAzureOpenAIChatCompletion(
                        deploymentName: this.Config.ModelName,
                        endpoint: azEndpoint,
                        apiKey: azApiKey,
                        serviceId: "azure-openai");
                }

                break;
            }

            default:
                throw new ArgumentOutOfRangeException("Unsupported LLM provider " + this.Config.LLMProvider);
        }

        return b.Build().GetRequiredService<IChatCompletionService>(this.Config.LLMProvider);
    }

    // Check text with Azure Content Safety
    private async Task<(bool isSafe, object report)> IsSafeAsync(
        string? text,
        CancellationToken cancellationToken)
    {
        Response<AnalyzeTextResult>? result = await this._contentSafety.AnalyzeTextAsync(text, cancellationToken).ConfigureAwait(false);

        bool isSafe = result.HasValue && result.Value.CategoriesAnalysis.All(x => x.Severity is 0);
        IEnumerable<string> report = result.HasValue ? result.Value.CategoriesAnalysis.Select(x => $"{x.Category}: {x.Severity}") : Array.Empty<string>();

        return (isSafe, report);
    }

    private Task LogChatHistoryAsInsight(
        Conversation conversation,
        CancellationToken cancellationToken)
    {
        Insight insight = new("history", "Chat History", conversation.ToHtmlString(this.Id));
        return this.SetConversationInsightAsync(conversation.Id, insight, cancellationToken);
    }

    #endregion
}
