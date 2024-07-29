# Semantic Workbench App Setup Guide

The Semantic Workbench app is a React/Typescript app integrated with the [Semantic Workbench](../service/README.md) backend service.

## Setup

1. Install [Node 20](https://nodejs.org/en/download)

2. Within the [`v1/app`](./) directory, install packages.

        cd semantic-workbench/v1/app
        npm install
        npm start

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
