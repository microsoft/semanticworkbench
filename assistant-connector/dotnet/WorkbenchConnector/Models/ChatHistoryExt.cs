// Copyright (c) Microsoft. All rights reserved.

using System.Text;
using Microsoft.SemanticKernel.ChatCompletion;

// ReSharper disable once CheckNamespace
namespace Microsoft.SemanticWorkbench.Connector;

public static class ChatHistoryExt
{
    public static string AsString(this ChatHistory history)
    {
        var result = new StringBuilder();
        foreach (var msg in history)
        {
            result.Append("[**").Append(msg.Role).Append("**] ");
            result.AppendLine(msg.Content);
        }

        return result.ToString();
    }
}
