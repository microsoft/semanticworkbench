// Copyright (c) Microsoft. All rights reserved.

using System.Text;
using Microsoft.SemanticWorkbench.Connector;

namespace AgentExample;

public static class ConnectorExtensions
{
    public static string GetParticipantName(this Conversation conversation, string id)
    {
        if (conversation.Participants.TryGetValue(id, out Participant? participant))
        {
            return participant.Name;
        }

        return "Unknown";
    }

    public static string ToHtmlString(
        this Conversation conversation,
        string assistantId)
    {
        var result = new StringBuilder();
        result.AppendLine("<style>");
        result.AppendLine("DIV.conversationHistory { padding: 0 20px 60px 20px; }");
        result.AppendLine("DIV.conversationHistory P { margin: 0 0 8px 0; }");
        result.AppendLine("</style>");
        result.AppendLine("<div class='conversationHistory'>");

        foreach (var msg in conversation.Messages)
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
                    .Append(conversation.GetParticipantName(msg.Sender.Id))
                    .AppendLine("</b><br/>");
            }

            result.AppendLine(msg.Content).AppendLine("</p>");
        }

        result.Append("</div>");

        return result.ToString();
    }
}
