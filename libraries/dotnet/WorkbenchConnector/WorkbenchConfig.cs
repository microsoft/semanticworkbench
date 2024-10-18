// Copyright (c) Microsoft. All rights reserved.

using System;

namespace Microsoft.SemanticWorkbench.Connector;

public class WorkbenchConfig
{
    /// <summary>
    /// Semantic Workbench endpoint.
    /// </summary>
    public string WorkbenchEndpoint { get; set; } = "http://localhost:3000";

    /// <summary>
    /// The endpoint of your service, where semantic workbench will send communications too.
    /// This should match hostname, port, protocol and path of the web service. You can use
    /// this also to route semantic workbench through a proxy or a gateway if needed.
    /// </summary>
    public string ConnectorEndpoint { get; set; } = "http://localhost:9001/myagents";

    /// <summary>
    /// Unique ID of the service. Semantic Workbench will store this event to identify the server
    /// so you should keep the value fixed to match the conversations tracked across service restarts.
    /// </summary>
    public string ConnectorId { get; set; } = Guid.NewGuid().ToString("D");

    /// <summary>
    /// Name of your agent service
    /// </summary>
    public string ConnectorName { get; set; } = ".NET Multi Agent Service";

    /// <summary>
    /// Description of your agent service.
    /// </summary>
    public string ConnectorDescription { get; set; } = "Multi-agent service for .NET agents";
}
