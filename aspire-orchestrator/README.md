# .NET Aspire Integratiuon

## Run Prerequisites

- [dotnet (8 or greater)](https://dotnet.microsoft.com/en-us/download)

## Deployment Prerequisites

- [Azure Developer CLI](https://learn.microsoft.com/en-us/azure/developer/azure-developer-cli/install-azd?tabs=winget-windows%2Cbrew-mac%2Cscript-linux)
- [dotnet (9 or greater)](https://dotnet.microsoft.com/en-us/download)
- [Python 3.8 or greater](https://www.python.org/downloads/)
- [NodeJs v18.12 or greater](https://nodejs.org/en/download/)

## Run with .NET Aspire

1. Clone the repository

```bash
make
cd aspire-orchestrator
dotnet run
```

## Deployment Steps with azd

1. Clone the repository
2. In the root folder, run
```bash
make
```
3. [Configure the app registration and configure workbenchapp and workbench service](../docs/CUSTOM_APP_REGISTRATION.md)
4. Authenticate with Azure Developer CLI
```bash
azd login
```
5. Create the infrastructure and deploy the application
```bash
azd up
```
6. Update the App Registration with the correct workbenchapp redirect URI