using System.Runtime.InteropServices;
using Microsoft.Extensions.Hosting;

namespace CommunityToolkit.Aspire.Hosting.Uvicorn;

public static class UvicornAppHostingExtensions
{
    public static IResourceBuilder<UvicornAppResource> AddUvicornApp(
        this IDistributedApplicationBuilder builder,
        string name,
        string projectDirectory,
        string scriptPath,
        params string[] scriptArgs)
    {
        ArgumentNullException.ThrowIfNull(builder);

        return builder.AddUvicornApp(name, scriptPath, projectDirectory, ".venv", scriptArgs);
    }

    private static IResourceBuilder<UvicornAppResource> AddUvicornApp(this IDistributedApplicationBuilder builder,
        string name,
        string scriptPath,
        string projectDirectory,
        string virtualEnvironmentPath,
        params string[] args)
    {
        ArgumentNullException.ThrowIfNull(builder);
        ArgumentNullException.ThrowIfNull(name);
        ArgumentNullException.ThrowIfNull(scriptPath);

        string wd = projectDirectory ?? Path.Combine("..", name);

        projectDirectory = PathNormalizer.NormalizePathForCurrentPlatform(Path.Combine(builder.AppHostDirectory, wd));

        var virtualEnvironment = new VirtualEnvironment(Path.IsPathRooted(virtualEnvironmentPath)
            ? virtualEnvironmentPath
            : Path.Join(projectDirectory, virtualEnvironmentPath));

        var instrumentationExecutable = virtualEnvironment.GetExecutable("opentelemetry-instrument");
        // var pythonExecutable = virtualEnvironment.GetRequiredExecutable("python");
        // var projectExecutable = instrumentationExecutable ?? pythonExecutable;

        string[] allArgs = args is { Length: > 0 }
            ? ["run", scriptPath, .. args]
            : ["run", scriptPath];

        var projectResource = new UvicornAppResource(name, projectDirectory);

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

public static class DockerFileExtensions
{
    public static IResourceBuilder<ExecutableResource> PublishAsDockerImage(this IResourceBuilder<ExecutableResource> builder,
        string? dockerContext = null,
        string? dockerFilePath = null,
        Action<IResourceBuilder<ContainerResource>>? configure = null)
    {
        if (!builder.ApplicationBuilder.ExecutionContext.IsPublishMode)
        {
            return builder;
        }

        // Bait and switch the ExecutableResource with a ContainerResource
        builder.ApplicationBuilder.Resources.Remove(builder.Resource);

        var container = new ExecutableContainerResource(builder.Resource);
        var cb = builder.ApplicationBuilder.AddResource(container);
        cb.WithImage(builder.Resource.Name);
        cb.WithDockerfile(contextPath: dockerContext ?? builder.Resource.WorkingDirectory, dockerfilePath: dockerFilePath);
        // Clear the runtime args
        cb.WithArgs(c => c.Args.Clear());

        configure?.Invoke(cb);

        return builder;
    }

    class ExecutableContainerResource(ExecutableResource er) : ContainerResource(er.Name)
    {
        public override ResourceAnnotationCollection Annotations => er.Annotations;
    }
}