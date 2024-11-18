# Deploy with .NET Aspire and azd

## Prerequisites

- [Azure Developer CLI](https://learn.microsoft.com/en-us/azure/developer/azure-developer-cli/install-azd?tabs=winget-windows%2Cbrew-mac%2Cscript-linux)
- [dotnet (8 or greater)](https://dotnet.microsoft.com/en-us/download)

## Steps

1. Clone the repository
2. In the root folder, run `make`
3. cd into the `workbench-service` folder
4. Activate the virtual environment
5. Run `uv sync`
6. [Configure the app registration and configure workbenchapp and workbench service](../docs/CUSTOM_APP_REGISTRATION.md)
7. Run `azd login` to authenticate with Azure DevOps
8. Run `azd up` to create the infrastructure and deploy the application