// Copyright (c) Microsoft. All rights reserved.

using System.Text.Json;
using Azure;
using Azure.AI.ContentSafety;
using Microsoft.Extensions.Logging.Abstractions;
using Microsoft.SemanticWorkbench.Connector;

namespace AgentExample02;

public class MyAgent : AgentBase
{
    // Agent settings
    public MyAgentConfig Config
    {
        get { return (MyAgentConfig)this.RawConfig; }
        private set { this.RawConfig = value; }
    }

    // Azure Content Safety
    private readonly ContentSafetyClient _contentSafety;

    /// <summary>
    /// Create a new agent instance
    /// </summary>
    /// <param name="agentId">Agent instance ID</param>
    /// <param name="agentName">Agent name</param>
    /// <param name="agentConfig">Agent configuration</param>
    /// <param name="workbenchConnector">Service containing the agent, used to communicate with Workbench backend</param>
    /// <param name="storage">Agent data storage</param>
    /// <param name="contentSafety">Azure content safety</param>
    /// <param name="kernel">Semantic Kernel</param>
    /// <param name="loggerFactory">App logger factory</param>
    public MyAgent(
        string agentId,
        string agentName,
        MyAgentConfig? agentConfig,
        WorkbenchConnector workbenchConnector,
        IAgentServiceStorage storage,
        ContentSafetyClient contentSafety,
        ILoggerFactory? loggerFactory = null)
        : base(
            workbenchConnector,
            storage,
            loggerFactory?.CreateLogger<MyAgent>() ?? new NullLogger<MyAgent>())
    {
        this.Id = agentId;
        this.Name = agentName;
        this.Config = agentConfig ?? new MyAgentConfig();
        this._contentSafety = contentSafety;
    }

    /// <inheritdoc />
    public override IAgentConfig GetDefaultConfig()
    {
        return new MyAgentConfig();
    }

    /// <inheritdoc />
    public override IAgentConfig? ParseConfig(object data)
    {
        return JsonSerializer.Deserialize<MyAgentConfig>(JsonSerializer.Serialize(data));
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

            // Support only the "say" command
            if (command.CommandName.ToLowerInvariant() != "say") { return; }

            // Update the chat history to include the message received
            await base.ReceiveMessageAsync(conversationId, command, cancellationToken).ConfigureAwait(false);

            // Check if we're replying to other agents
            if (!this.Config.ReplyToAgents && command.Sender.Role == "assistant") { return; }

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
    public override Task ReceiveMessageAsync(
        string conversationId,
        Message message,
        CancellationToken cancellationToken = default)
    {
        switch (this.Config.Behavior.ToLowerInvariant())
        {
            case "echo": return this.EchoExampleAsync(conversationId, message, cancellationToken);
            case "reverse": return this.ReverseExampleAsync(conversationId, message, cancellationToken);
            case "safety check": return this.SafetyCheckExampleAsync(conversationId, message, cancellationToken);
            case "markdown sample": return this.MarkdownExampleAsync(conversationId, message, cancellationToken);
            case "html sample": return this.HTMLExampleAsync(conversationId, message, cancellationToken);
            case "code sample": return this.CodeExampleAsync(conversationId, message, cancellationToken);
            case "json sample": return this.JSONExampleAsync(conversationId, message, cancellationToken);
            case "mermaid sample": return this.MermaidExampleAsync(conversationId, message, cancellationToken);
            case "music sample": return this.MusicExampleAsync(conversationId, message, cancellationToken);
            case "none": return this.NoneExampleAsync(conversationId, message, cancellationToken);
            default: return this.NoneExampleAsync(conversationId, message, cancellationToken);
        }
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

    private async Task EchoExampleAsync(
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

            // Ignore empty messages
            if (string.IsNullOrWhiteSpace(message.Content)) { return; }

            // Create the answer content
            var (inputIsSafe, report) = await this.IsSafeAsync(message.Content, cancellationToken).ConfigureAwait(false);
            var answer = inputIsSafe
                ? Message.CreateChatMessage(this.Id, message.Content)
                : Message.CreateChatMessage(this.Id, "I'm not sure how to respond to that.", report);

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

    private async Task ReverseExampleAsync(
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

            // Ignore empty messages
            if (string.IsNullOrWhiteSpace(message.Content)) { return; }

            // Create the answer content
            var (inputIsSafe, report) = await this.IsSafeAsync(message.Content, cancellationToken).ConfigureAwait(false);
            var answer = inputIsSafe
                ? Message.CreateChatMessage(this.Id, $"{new string(message.Content.Reverse().ToArray())}")
                : Message.CreateChatMessage(this.Id, "I'm not sure how to respond to that.", report);

            // Check the output too
            var (outputIsSafe, reportOut) = await this.IsSafeAsync(answer.Content, cancellationToken).ConfigureAwait(false);
            if (!outputIsSafe)
            {
                answer = Message.CreateChatMessage(this.Id, "Sorry I won't process that.", reportOut);
            }

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

    private Task LogChatHistoryAsInsight(
        Conversation conversation,
        CancellationToken cancellationToken)
    {
        var insight = new Insight("history", "Chat History", conversation.ToHtmlString(this.Id));
        return this.SetConversationInsightAsync(conversation.Id, insight, cancellationToken);
    }

    private async Task SafetyCheckExampleAsync(
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

            // Create the answer content
            Message answer;
            Response<AnalyzeTextResult>? result = await this._contentSafety.AnalyzeTextAsync(message.Content, cancellationToken).ConfigureAwait(false);
            if (!result.HasValue)
            {
                answer = Message.CreateChatMessage(
                    this.Id,
                    "Sorry, something went wrong, I couldn't analyze the message.",
                    "The request to Azure Content Safety failed and returned NULL");
            }
            else
            {
                bool isOffensive = result.Value.CategoriesAnalysis.Any(x => x.Severity is > 0);
                IEnumerable<string> report = result.Value.CategoriesAnalysis.Select(x => $"{x.Category}: {x.Severity}");

                answer = Message.CreateChatMessage(
                    this.Id,
                    isOffensive ? "Offensive content detected" : "OK",
                    report);
            }

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

    private async Task MarkdownExampleAsync(
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

            // Prepare answer using Markdown syntax
            const string MarkdownContent = """
                                           # Using Semantic Workbench with .NET Agents

                                           This project provides an example of testing your agent within the **Semantic Workbench**.

                                           ## Project Overview

                                           The sample project utilizes the `WorkbenchConnector` library, enabling you to focus on agent development and testing.

                                           Semantic Workbench allows mixing agents from different frameworks and multiple instances of the same agent.
                                           The connector can manage multiple agent instances if needed, or you can work with a single instance if preferred.
                                           To integrate agents developed with other frameworks, we recommend isolating each agent type with a dedicated web service, ie a dedicated project.
                                           """;
            var answer = Message.CreateChatMessage(this.Id, MarkdownContent);

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

    private async Task HTMLExampleAsync(
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

            // Create the answer content
            const string HTMLExample = """
                                       <h1>Using Semantic Workbench with .NET Agents</h1>

                                       <p>This project provides an example of testing your agent within the <b>Semantic Workbench</b>.</p>

                                       <h2>Project Overview</h2>

                                       <p>The sample project utilizes the <pre>WorkbenchConnector</pre> library, enabling you to focus on agent development and testing.</p>

                                       <p>Semantic Workbench allows mixing agents from different frameworks and multiple instances of the same agent.
                                       The connector can manage multiple agent instances if needed, or you can work with a single instance if preferred.
                                       To integrate agents developed with other frameworks, we recommend isolating each agent type with a dedicated web service, ie a dedicated project.</p>
                                       """;
            var answer = Message.CreateChatMessage(this.Id, HTMLExample, contentType: "text/html");

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

    private async Task CodeExampleAsync(
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

            // Create the answer content
            const string CodeExample = """
                                       How to instantiate SK with OpenAI:

                                       ```csharp
                                       // Semantic Kernel with OpenAI
                                       var openAIKey = appBuilder.Configuration.GetSection("OpenAI").GetValue<string>("ApiKey")
                                                       ?? throw new ArgumentNullException("OpenAI config not found");
                                       var openAIModel = appBuilder.Configuration.GetSection("OpenAI").GetValue<string>("Model")
                                                         ?? throw new ArgumentNullException("OpenAI config not found");
                                       appBuilder.Services.AddSingleton<Kernel>(_ => Kernel.CreateBuilder()
                                           .AddOpenAIChatCompletion(openAIModel, openAIKey)
                                           .Build());
                                       ```
                                       """;
            var answer = Message.CreateChatMessage(this.Id, CodeExample);

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

    private async Task MermaidExampleAsync(
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

            // Create the answer content
            const string MermaidContentExample = """
                                                 ```mermaid
                                                 gitGraph:
                                                     commit "Ashish"
                                                     branch newbranch
                                                     checkout newbranch
                                                     commit id:"1111"
                                                     commit tag:"test"
                                                     checkout main
                                                     commit type: HIGHLIGHT
                                                     commit
                                                     merge newbranch
                                                     commit
                                                     branch b2
                                                     commit
                                                 ```
                                                 """;
            var answer = Message.CreateChatMessage(this.Id, MermaidContentExample);

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

    private async Task MusicExampleAsync(
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

            // Create the answer content
            const string ABCContentExample = """
                                             ```abc
                                             X:1
                                             T:Twinkle, Twinkle, Little Star
                                             M:4/4
                                             L:1/4
                                             K:C
                                             C C G G | A A G2 | F F E E | D D C2 |
                                             G G F F | E E D2 | G G F F | E E D2 |
                                             C C G G | A A G2 | F F E E | D D C2 |
                                             ```
                                             """;
            var answer = Message.CreateChatMessage(this.Id, ABCContentExample);

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

    private async Task JSONExampleAsync(
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

            // Ignore empty messages
            if (string.IsNullOrWhiteSpace(message.Content)) { return; }

            // Create the answer content
            const string JSONExample = """
                                       {
                                         "name": "Devis",
                                         "age": 30,
                                         "email": "noreply@some.email",
                                         "address": {
                                           "street": "123 Main St",
                                           "city": "Anytown",
                                           "state": "CA",
                                           "zip": "123456"
                                         }
                                       }
                                       """;
            var answer = Message.CreateChatMessage(this.Id, JSONExample, contentType: "application/json");

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

    private async Task NoneExampleAsync(
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

            // Exit without doing anything
        }
        finally
        {
            this.Log.LogTrace("Reset agent status");
            await this.ResetAgentStatusAsync(conversationId, cancellationToken).ConfigureAwait(false);
        }
    }
}
