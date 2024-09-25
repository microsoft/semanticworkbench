# Semantic Workbench App Setup Guide

The Semantic Workbench app is a React/Typescript app integrated with the [Semantic Workbench](../service/README.md) backend service.

Follow the [setup guide](../../../docs/SETUP.md) to configure your environment.

## Running Workbench App from VS Code

To debug in VSCode, View->Run, "semantic-workbench-app"

## Running Workbench App from the Command Line

In the [app directory](./)

```sh
npm start
```

Note: you might be prompted for admin credentials, for the SSL certificates used by the app.

## Extra information

### Scripts

-   `npm start` - start dev server and open browser
-   `npm build` - build for production
-   `npm preview` - locally preview production build

### More info

-   [Message Metadata](./docs/MESSAGE_METADATA.md)
-   [Message Types](./docs/MESSAGE_TYPES.md)
-   [State Inspectors](./docs/STATE_INSPECTORS.md)
