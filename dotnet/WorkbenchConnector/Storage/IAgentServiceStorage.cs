// Copyright (c) Microsoft. All rights reserved.

// ReSharper disable once CheckNamespace
namespace Microsoft.SemanticWorkbench.Connector;

public interface IAgentServiceStorage
{
    Task SaveAgentAsync(AgentBase agent, CancellationToken cancellationToken = default);
    Task DeleteAgentAsync(AgentBase agent, CancellationToken cancellationToken = default);
    Task<List<AgentInfo>> GetAllAgentsAsync(CancellationToken cancellationToken = default);

    Task SaveConversationAsync(Conversation conversation, CancellationToken cancellationToken = default);
    Task<Conversation?> GetConversationAsync(string conversationId, string agentId, CancellationToken cancellationToken = default);
    Task DeleteConversationAsync(string conversationId, string agentId, CancellationToken cancellationToken = default);
    Task DeleteConversationAsync(Conversation conversation, CancellationToken cancellationToken = default);

    Task<List<Insight>> GetAllInsightsAsync(string agentId, string conversationId, CancellationToken cancellationToken = default);
    Task SaveInsightAsync(string agentId, string conversationId, Insight insight, CancellationToken cancellationToken = default);
    Task DeleteInsightAsync(string agentId, string conversationId, string insightId, CancellationToken cancellationToken = default);
}
