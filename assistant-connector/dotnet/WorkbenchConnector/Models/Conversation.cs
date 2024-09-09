// Copyright (c) Microsoft. All rights reserved.

using System.Text;
using System.Text.Json.Serialization;
using Microsoft.SemanticKernel.ChatCompletion;

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
    public Dictionary<string, Participant> Participants { get; set; } = new();

    [JsonPropertyName("messages")]
    [JsonPropertyOrder(3)]
    public List<Message> Messages { get; set; } = new();

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

    public ChatHistory ToChatHistory(string assistantId, string systemPrompt)
    {
        var result = new ChatHistory(systemPrompt);

        foreach (Message msg in this.Messages)
        {
            if (msg.Sender.Id == assistantId)
            {
                result.AddAssistantMessage(msg.Content!);
            }
            else
            {
                result.AddUserMessage($"[{this.GetParticipantName(msg.Sender.Id)}] {msg.Content}");
            }
        }

        return result;
    }

    public string ToHtmlString(string assistantId)
    {
        var result = new StringBuilder();
        result.AppendLine("<style>");
        result.AppendLine("DIV.conversationHistory { padding: 0 20px 60px 20px; }");
        result.AppendLine("DIV.conversationHistory P { margin: 0 0 8px 0; }");
        result.AppendLine("</style>");
        result.AppendLine("<div class='conversationHistory'>");

        foreach (var msg in this.Messages)
        {
            result.AppendLine("<p>");
            if (msg.Sender.Id == assistantId)
            {
                result.AppendLine("<b>Assistant</b><br/>");
            }
            else
            {
                result
                    .Append("<b>")
                    .Append(this.GetParticipantName(msg.Sender.Id))
                    .AppendLine("</b><br/>");
            }

            result.AppendLine(msg.Content).AppendLine("</p>");
        }

        result.Append("</div>");

        return result.ToString();
    }

    // TODO: the list of participants is incomplete, because agents see only participants being added
    private string GetParticipantName(string id)
    {
        if (this.Participants.TryGetValue(id, out Participant? participant))
        {
            return participant.Name;
        }

        return "Unknown";
    }
}
