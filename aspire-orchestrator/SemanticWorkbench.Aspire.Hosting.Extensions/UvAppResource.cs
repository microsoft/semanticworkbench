using System;
using System.Diagnostics.CodeAnalysis;
using System.Runtime.CompilerServices;

namespace Aspire.Hosting.ComponentModel;

public class UvAppResource(string name, string workingDirectory)
    : ExecutableResource(name, "uv", workingDirectory), IResourceWithServiceDiscovery
{
    internal const string HttpEndpointName = "http";
}
