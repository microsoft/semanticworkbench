using System;
using System.Diagnostics.CodeAnalysis;
using System.Runtime.CompilerServices;

namespace CommunityToolkit.Aspire.Hosting.Uvicorn;

public class UvicornAppResource(string name, string workingDirectory)
    : ExecutableResource(name, "uv", workingDirectory), IResourceWithServiceDiscovery
{
    internal const string HttpEndpointName = "http";
}
