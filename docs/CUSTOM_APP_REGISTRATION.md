# Custom app registration

The code in this repo is intended to allow for quick-to-try usage. This includes a hard-coded app registration details in the app and service. While this works for minimal setup for development and usage in localhost environments, you will need to create your own Azure app registration and update the app and service files with the new app registration details if you want to use this in a hosted environment.

**DISCLAIMER**: The security considerations of hosting a service with a public endpoint are beyond the scope of this document. Please ensure you understand the implications of hosting a service before doing so. It is **not recommended** to host a publicly available instance of the Semantic Workbench app.

## Create a new Azure app registration

### Prerequisites

In order to complete these steps, you will need to have an Azure account. If you don't have an Azure account, you can create a free account by navigating to https://azure.microsoft.com/en-us/free.

App registration is a free service, but you may need to provide a credit card for verification purposes.

### Steps

- Navigate to the [Azure portal > App registrations](https://portal.azure.com/#view/Microsoft_AAD_RegisteredApps/ApplicationsListBlade)
  - Click on `New registration` and fill in the details
  - Name: `Semantic Workbench` (or any name you prefer)
  - Supported account types: `Accounts in any organizational directory and personal Microsoft accounts`
  - Redirect URI: `Single-page application (SPA)` & `https://<YOUR_HOST>`
    - Example (if using [Codespaces](../.devcontainer/README.md)): `https://<YOUR_CODESPACE_HOST>-4000.app.github.dev`
  - Click on `Register`
- View the `Overview` page for the newly registered app and copy the `Application (client) ID` for the next steps

## Update your app and service files with the new app registration details

Edit the following files with the new app registration details:

- Semantic Workbench app: [constants.ts](../semantic-workbench/v1/app/src/Constants.ts)

  - Update the `msal.auth.clientId` with the `Application (client) ID`

- Semantic Workbench service: [middleware.py](../semantic-workbench/v1/service/semantic-workbench-service/semantic_workbench_service/middleware.py)
  - Update the `allowed_app_ids` with the `Application (client) ID`

## TODO

- [ ] Update the codebase to allow app registration details to be passed in as environment variables
