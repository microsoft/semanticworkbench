# Using GitHub Codespaces with devcontainers for Semantic Workbench

- Create app registration at https://portal.azure.com
  - Manage > Authentication > Single-page application > Redirect URI's
  - Add `https://<YOUR_CODESPACE_HOST>-4000.app.github.dev`
  - Copy the Application (client) ID from Overview
- Update `constants.ts` with the Application (client) ID
- Update `middleware.py` with the Application (client) ID
- Use VS Code > Run and Debug > `Semantic Workbench` to start both the app and the service
- After launching semantic-workbench-service, go to Ports and make 3000 public

## TODO

- [ ] Add support for reading Application (client) ID from environment variables
- [ ] Improve this README with details on App Registration setup, and more detailed steps
