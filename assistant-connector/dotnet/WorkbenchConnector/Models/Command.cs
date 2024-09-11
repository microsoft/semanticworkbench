// Copyright (c) Microsoft. All rights reserved.

using System;

// ReSharper disable once CheckNamespace
namespace Microsoft.SemanticWorkbench.Connector;

public class Command : Message
{
    public string CommandName { get; set; }

    public string CommandParams { get; set; }

    public Command(Message message)
    {
        this.Id = message.Id;
        this.MessageType = message.MessageType;
        this.ContentType = message.ContentType;
        this.Content = message.Content;
        this.Timestamp = message.Timestamp;
        this.Sender = message.Sender;
        this.Metadata = message.Metadata;

        var p = this.Content?.Split(" ", 2, StringSplitOptions.TrimEntries);
        this.CommandName = p?.Length > 0 ? p[0].TrimStart('/') : "";
        this.CommandParams = p?.Length > 1 ? p[1] : "";
    }
}
