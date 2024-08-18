# Local Assistant / Remote Semantic Workbench

This guide will walk you through the process of creating a local assistant that communicates with a remote Semantic Workbench instance.

This guide assumes you have already set up a Semantic Workbench instance and have a basic understanding of how to create an assistant.

## Prerequisites

- A Semantic Workbench instance running on a remote server (ex: `https://contoso-semantic-workbench.azurewebsites.net`)
- A local assistant project that has been tested with a local Semantic Workbench instance

## Steps

[Microsoft Dev Tunnel](https://learn.microsoft.com/en-us/azure/developer/dev-tunnels/) is a tool that allows you to securely expose your local development environment to the cloud. This is useful for testing your local assistant with a remote Semantic Workbench instance.

The following steps will guide you through the process of setting up a tunnel to your local machine.

**Note:** The tunnel will only be accessible while it is running, so you will need to keep the tunnel running while testing and may not want to share the URL with others without being explicit about the availability.

**SECURITY NOTE:** Be aware that the tunnel will expose your local machine to the internet and allow anonymous access to the assistant. Make sure you are aware of the security implications and take appropriate precautions.

- [Install](https://learn.microsoft.com/en-us/azure/developer/dev-tunnels/get-started?tabs=windows#install)
  - `winget install Microsoft.devtunnel` (PowerShell)
  - `brew install --cask devtunnel` (macOS)
- [Login](https://learn.microsoft.com/en-us/azure/developer/dev-tunnels/get-started?tabs=windows#install)
  - `devtunnel user login`
  - Log in with your Microsoft AAD account
- [Host a tunnel](https://learn.microsoft.com/en-us/azure/developer/dev-tunnels/get-started?tabs=windows#host)
  - `devtunnel host -p 3001 --allow-anonymous --protocol http`
  - Replace `3001` with the port your local assistant is running on
  - After starting the host, note the `Connect via browser` URL - this URL will be used to connect to your local assistant from the remote Semantic Workbench instance
  - Alternatively, this may be done via the `Terminal` > `Run task...` command in VS Code if using the provided `tasks.json`:
    - `Terminal` > `Run Task...` > `start devtunnel`
- Create assistant service registration in remote Semantic Workbench
  - Launch the remote Semantic Workbench
  - Go to `Settings` > `Create Assistant Service Registration`
  - Fill in the required fields, check `Include in listing` if you want to share the assistant with others
  - Copy the `Registration ID` for later use
  - Save the assistant
- Launch the assistant locally with the tunnel URL
  - Assumes you have a local assistant project with `launch.json` configured to run the assistant locally
  - Create a `.env` file in the root of the assistant project with the contents from the `.env.example` file
    - Uncomment the section for `Assistant Service Registration` and fill in the id and key from the registration created in the previous step
  - `Run & Debug` (ctrl+shift+D) > `<assistant_name> for devtunnel`
  - When prompted, enter the tunnel URL from above as the `Assistant Service URL`
  - The assistant should now be accessible from the remote Semantic Workbench instance
- Connect to the assistant:
  - When creating a new assistant instance in the Semantic Workbench, this assistant will be available if the registration was shared
  - If it was not shared, you can choose `Manual entry` and enter the `Registration ID` from the registration created in the previous step
  - Remember that the URL will be accessible only while the tunnel is running, so you will need to keep the tunnel running while testing and may not want to share the Registration ID with others without being explicit about the availability
