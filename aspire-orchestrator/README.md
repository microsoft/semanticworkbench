# .NET Aspire Integration

## Run Prerequisites

- [dotnet (8 or greater)](https://dotnet.microsoft.com/download)
- [Python 3.8 or greater](https://www.python.org/downloads)
- [NodeJs v18.12 or greater](https://nodejs.org/en/download)

## Deployment Prerequisites

- [Azure Developer CLI](https://learn.microsoft.com/azure/developer/azure-developer-cli/install-azd)
- [Docker for Desktop](https://docs.docker.com/get-started/introduction/get-docker-desktop)
- [dotnet (9 or greater)](https://dotnet.microsoft.com/download)
- [Python 3.8 or greater](https://www.python.org/downloads)
- [NodeJs v18.12 or greater](https://nodejs.org/en/download)

## Run with .NET Aspire

1.  Make sure your workstation trusts
    [ASP.NET Core HTTPS development certificate](https://learn.microsoft.com/en-us/aspnet/core/security/enforcing-ssl?#trust-the-aspnet-core-https-development-certificate)

        dotnet dev-certs https --trust

2.  Clone the repository

        make
        cd aspire-orchestrator
        cd Aspire.AppHost
        dotnet run

## Deployment Steps with azd

1.  Clone the repository

2.  [Configure the Entra app registration](../docs/CUSTOM_APP_REGISTRATION.md).
    Copy the Entra **Application Id** and **Tenant Id** into
    `aspire-orchestrator/Aspire.AppHost/appsettings.json` file.

    If your Entra App allows both organizational and personal accounts
    use `common` as Tenant Id, e.g. setting
    `"Authority": "https://login.microsoftonline.com/common"`.

        {
          "EntraID": {
            "ClientId": "<CLIENT_ID>",
            "Authority": "https://login.microsoftonline.com/<TENANT_ID>"
          }
        }

3.  In the root folder of the repository, run

        make

4.  Authenticate with Azure Developer CLI

        azd login

5.  Generate the Azure config files required in the next step

        azd init --from-code --environment semanticworkbench

6.  Create Azure resources and deploy the application

        azd up

    When asked for "**authority**", enter the same value set in appsettings.json.

    When asked for "**clientId**", enter the same value set in appsettings.json.

    These values are stored as Environment Variables and can be modified in Azure
    Portal if needed.

    The deployment will take a few minutes to complete, taking care also of
    creating and deploying the required docker images.

7.  After the deployment is complete, a few URLs will be printed, in particular
    the Aspire Dashboard URL and Semantic Workbench App URL.

    Copy the `service workbenchapp` endpoint value for the next step:
    | ![Image](https://github.com/user-attachments/assets/0aae7518-bfa6-4f76-962a-df3d152e0155) |
    |:--:|

8.  Update the [Entra App Registration](https://portal.azure.com/#view/Microsoft_AAD_IAM/ActiveDirectoryMenuBlade/~/RegisteredApps),
    adding the URL from the previous step as one of the SPA Redirection URIs:
    | ![Image](https://github.com/user-attachments/assets/e709ee12-a3ef-4be3-9f2d-46d33c929f42) |
    |:-:|

9.  Open your browser and navigate to the same URL.
