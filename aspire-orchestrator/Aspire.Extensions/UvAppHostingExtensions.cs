// Copyright (c) Microsoft. All rights reserved.

using Aspire.Hosting.ComponentModel;
using Aspire.Hosting.Extensions;

namespace Aspire.Hosting;

public static class UvAppHostingExtensions
{
    public static IResourceBuilder<UvAppResource> AddUvApp(
        this IDistributedApplicationBuilder builder,
        string name,
        string projectDirectory,
        string scriptPath,
        params string[] scriptArgs)
    {
        ArgumentNullException.ThrowIfNull(builder);

        return builder.AddUvApp(name, scriptPath, projectDirectory, ".venv", scriptArgs);
    }

    private static IResourceBuilder<UvAppResource> AddUvApp(this IDistributedApplicationBuilder builder,
        string name,
        string scriptPath,
        string? projectDirectory,
        string virtualEnvironmentPath,
        params string[] args)
    {
        ArgumentNullException.ThrowIfNull(builder);
        ArgumentNullException.ThrowIfNull(name);
        ArgumentNullException.ThrowIfNull(scriptPath);

        string wd = projectDirectory ?? Path.Combine("..", name);

        projectDirectory = Path.Combine(builder.AppHostDirectory, wd).NormalizePathForCurrentPlatform();

        var virtualEnvironment = new VirtualEnvironment(Path.IsPathRooted(virtualEnvironmentPath)
            ? virtualEnvironmentPath
            : Path.Join(projectDirectory, virtualEnvironmentPath));

        var instrumentationExecutable = virtualEnvironment.GetExecutable("opentelemetry-instrument");
        // var pythonExecutable = virtualEnvironment.GetRequiredExecutable("python");
        // var projectExecutable = instrumentationExecutable ?? pythonExecutable;

        string[] allArgs = args is { Length: > 0 }
            ? ["run", "--frozen", scriptPath, .. args]
            : ["run", "--frozen", scriptPath];

        var projectResource = new UvAppResource(name, projectDirectory);

        var resourceBuilder = builder.AddResource(projectResource)
            .WithArgs(allArgs)
            .WithArgs(context =>
            {
                // If the project is to be automatically instrumented, add the instrumentation executable arguments first.
                if (!string.IsNullOrEmpty(instrumentationExecutable))
                {
                    AddOpenTelemetryArguments(context);

                    // // Add the python executable as the next argument so we can run the project.
                    // context.Args.Add(pythonExecutable!);
                }
            });

        if (!string.IsNullOrEmpty(instrumentationExecutable))
        {
            resourceBuilder.WithOtlpExporter();

            // Make sure to attach the logging instrumentation setting, so we can capture logs.
            // Without this you'll need to configure logging yourself. Which is kind of a pain.
            resourceBuilder.WithEnvironment("OTEL_PYTHON_LOGGING_AUTO_INSTRUMENTATION_ENABLED", "true");
        }

        return resourceBuilder;
    }

    private static void AddOpenTelemetryArguments(CommandLineArgsCallbackContext context)
    {
        context.Args.Add("--traces_exporter");
        context.Args.Add("otlp");

        context.Args.Add("--logs_exporter");
        context.Args.Add("console,otlp");

        context.Args.Add("--metrics_exporter");
        context.Args.Add("otlp");
    }
}
