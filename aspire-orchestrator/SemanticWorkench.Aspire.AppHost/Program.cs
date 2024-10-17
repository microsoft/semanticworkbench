var builder = DistributedApplication.CreateBuilder(args);

// var service = builder.AddPythonApp("service", projectDirectory: Path.Combine("..", "..", "workbench-service"), scriptPath: "start.py")
//     .WithHttpEndpoint(targetPort: 3000);

var service = builder.AddExecutable("assistant", @".\.venv\Scripts\start-semantic-workbench-service.exe", Path.Combine("..", "..", "workbench-service"))
    .WithHttpEndpoint(targetPort: 3000);

builder.AddViteApp("app", workingDirectory: Path.Combine("..", "..", "workbench-app"), packageManager: "pnpm")
    .WithPnpmPackageInstallation()
    .WithHttpsEndpoint(env: "PORT")
    .WaitFor(service);

builder.Build().Run();