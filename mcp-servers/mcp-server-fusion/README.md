# Fusion MCP Server

Fusion MCP Server for help creating 3D models

This is a [Model Context Protocol](https://github.com/modelcontextprotocol) (MCP) server project.

## Setup and Installation

Simply run:

```bash
pip install -r requirements.txt --target ./mcp_server_fusion/vendor
```

To create the virtual environment and install dependencies.

### Running the Server

- Open Autodesk Fusion
- Utilities > Add-Ins > Scripts and Add-Ins...
- Select the Add-Ins tab
- Click the My AddIns "+" icon to add a new Add-In
- Choose the _main project directory_
  - This is the folder that contains [FusionMCPServerAddIn.py](./FusionMCPServerAddIn.py)
- After added, select `FusionMCPServerAddIn` and click `Run`
- Select `Run on Startup` to have the server start automatically when Fusion starts
- The server will start silently, you can test it from your terminal via:

```bash
curl -N http://127.0.0.1:6050/sse
```

Which should return something similar to:

```
C:\>curl -N http://127.0.0.1:6010/sse
event: endpoint
data: /messages?sessionId=947e3ec6-7d10-442f-af8e-e8fe9779f285
```

Use `Ctrl+C` to disconnect the curl command.

### Debugging the Server

To run the server in debug mode, open the Scripts and Add-Ins dialog, select the `FusionMCPServerAddIn` and click `Debug`.
This will launch VS Code with the project open. Use the `F5` or `Run & Debug` button and select the `mcp-servers:mcp-server-fusion (attach)` configuration and click `Start Debugging`. This will attach to the running Fusion instance and allow you to debug the server. Wait until you see that the server is listening before attempting to connect.

```
c:\Users\<your_user>\AppData\Roaming\Autodesk\Autodesk Fusion 360\API\AddIns\mcp-server-fusion
Starting MCP Server add-in
Starting MCP server thread
MCP Server add-in started successfully
INFO:     Started server process [43816]
INFO:     Waiting for application startup.
INFO:     Application startup complete.
INFO:     Uvicorn running on http://0.0.0.0:6050 (Press CTRL+C to quit)
```

## Client Configuration

To use this MCP server in your setup, consider the following configuration:

### SSE

The SSE URL is:

```bash
http://127.0.0.1:6050/sse
```

```json
{
  "mcpServers": {
    "mcp-server-fusion": {
      "command": "http://127.0.0.1:6050/sse",
      "args": []
    }
  }
}
```

Here are some extra instructions to consider adding to your assistant configuration, but feel free to experiment further:

```
When creating models, remember the following:
- Z is vertical, X is horizontal, and Y is depth
- The top plane for an entity is an XY plane, at the Z coordinate of the top of the entity
- The bottom plane for an entity is an XY plane, at the Z coordinate of the bottom of the entity
- The front plane for an entity is an XZ plane, at the Y coordinate of the front of the entity
- The back plane for an entity is an XZ plane, at the Y coordinate of the back of the entity
- The left plane for an entity is a YZ plane, at the X coordinate of the left of the entity
- The right plane for an entity is a YZ plane, at the X coordinate of the right of the entity
- Remember to always use the correct plane and consider the amount of adjustment on the 3rd plane necessary
```
