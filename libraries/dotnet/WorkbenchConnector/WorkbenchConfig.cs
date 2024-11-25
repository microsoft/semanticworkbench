// Copyright (c) Microsoft. All rights reserved.

using System;

namespace Microsoft.SemanticWorkbench.Connector;

public class WorkbenchConfig
{
    /// <summary>
    /// Semantic Workbench endpoint.
    /// </summary>
    public string WorkbenchEndpoint { get; set; } = "http://127.0.0.1:3000";

    /// <summary>
    /// The host where the connector receives requests sent by the workbench.
    /// Locally, this is usually "http://127.0.0.1:[some port]"
    /// On Azure, this will be something like "https://contoso.azurewebsites.net"
    /// Leave this setting empty to use "127.0.0.1" and autodetect the port in use.
    /// You can use an env var to set this value, e.g. Workbench__ConnectorHost=https://contoso.azurewebsites.net
    /// </summary>
    public string ConnectorHost { get; set; } = string.Empty;

    /// <summary>
    /// This is the prefix of all the endpoints exposed by the connector
    /// </summary>
    public string ConnectorApiPrefix { get; set; } = "/myagents";

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
