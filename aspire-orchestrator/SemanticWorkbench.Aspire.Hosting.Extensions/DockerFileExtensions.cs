// Copyright (c) Microsoft. All rights reserved.

namespace Aspire.Hosting;

public static class DockerFileExtensions
{
    public static IResourceBuilder<ExecutableResource> PublishAsDockerImage(this IResourceBuilder<ExecutableResource> builder,
        string? dockerContext = null,
        string? dockerFilePath = "Dockerfile",
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