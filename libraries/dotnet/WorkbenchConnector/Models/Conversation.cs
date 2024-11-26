// Copyright (c) Microsoft. All rights reserved.

using System.Collections.Generic;
using System.Linq;
using System.Text.Json.Serialization;

// ReSharper disable once CheckNamespace
namespace Microsoft.SemanticWorkbench.Connector;

public class Conversation
{
    [JsonPropertyName("id")]
    [JsonPropertyOrder(0)]
    public string Id { get; set; } = string.Empty;

    [JsonPropertyName("agent_id")]
    [JsonPropertyOrder(1)]
    public string AgentId { get; set; } = string.Empty;

    [JsonPropertyName("participants")]
    [JsonPropertyOrder(2)]
    public Dictionary<string, Participant> Participants { get; set; } = [];

    [JsonPropertyName("messages")]
    [JsonPropertyOrder(3)]
    public List<Message> Messages { get; set; } = [];

    public Conversation()
    {
    }

    public Conversation(string id, string agentId)
    {
        this.Id = id;
        this.AgentId = agentId;
    }

    public void AddParticipant(Participant participant)
    {
        this.Participants[participant.Id] = participant;
    }

    public void RemoveParticipant(Participant participant)
    {
        this.Participants.Remove(participant.Id, out _);
    }

    public void AddMessage(Message? msg)
    {
        if (msg == null) { return; }

        this.Messages.Add(msg);
    }

    public void RemoveMessage(Message? msg)
    {
        if (msg == null) { return; }

        this.Messages = this.Messages.Where(x => x.Id != msg.Id).ToList();
    }
}
