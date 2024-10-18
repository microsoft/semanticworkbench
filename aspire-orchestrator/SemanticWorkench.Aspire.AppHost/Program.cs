var builder = DistributedApplication.CreateBuilder(args);

// var service = builder.AddPythonApp("service", projectDirectory: Path.Combine("..", "..", "workbench-service"), scriptPath: "start.py")
//     .WithHttpEndpoint(targetPort: 3000);

var workbenchService = builder.AddExecutable("worbenchservice", @".\.venv\Scripts\start-semantic-workbench-service.exe", Path.Combine("..", "..", "workbench-service"))
    .WithHttpEndpoint(targetPort: 3000, isProxied: true)
    .WithHttpHealthCheck("/");
var workbenchServiceEndpoint = workbenchService.GetEndpoint("http");

var agent3 = builder.AddProject<Projects.dotnet_03_simple_chatbot>("agent3")
    .WithReference(workbenchServiceEndpoint)
    .WaitFor(workbenchService);

agent3.WithReference(agent3);

builder.AddViteApp("workbenchapp", workingDirectory: Path.Combine("..", "..", "workbench-app"), packageManager: "pnpm")
    .WithPnpmPackageInstallation()
    .WithHttpsEndpoint(env: "PORT")
    .WithReference(workbenchServiceEndpoint)
    .WaitFor(workbenchService);

builder.Build().Run();