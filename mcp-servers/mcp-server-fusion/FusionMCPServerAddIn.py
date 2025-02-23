import adsk.core, adsk.fusion, adsk.cam
import threading
import traceback

# Global flag to signal the MCP server thread to stop.
mcp_running = True
mcp_thread = None

def start_mcp_server():
    from .mcp_server.server import create_mcp_server  # our existing function in mcp-server-fusion
    try:
        # Create the MCP server instance.
        mcp = create_mcp_server()
        # Set the server to use SSE transport and a chosen port.
        # Here, we explicitly set the port in the server settings.
        mcp.settings.port = 6050
        # Run the MCP server; this call will block until the server stops.
        mcp.run(transport='sse')
    except Exception as e:
        app = adsk.core.Application.get()
        ui = app.userInterface
        ui.messageBox(f'Error in MCP server thread: {traceback.format_exc()}')

def run(context):
    global mcp_running, mcp_thread
    app = adsk.core.Application.get()
    ui  = app.userInterface
    try:
        # Start the background thread to run the MCP server.
        mcp_running = True
        mcp_thread = threading.Thread(target=start_mcp_server, daemon=True)
        mcp_thread.start()
        ui.messageBox('Fusion MCP Server launched in background.')
    except Exception as e:
        ui.messageBox(f'Failed to start background MCP server: {e}')

def stop(context):
    global mcp_running, mcp_thread
    app = adsk.core.Application.get()
    ui = app.userInterface
    try:
        # Signal the background thread to stop.
        mcp_running = False
        # In our simple setup, assuming the MCP server checks for cancellation.
        # If needed, you might adjust the FastMCP server to poll the mcp_running flag.
        ui.messageBox('Fusion MCP Server add-in stopping. Please wait.')
        # Optionally, join the thread briefly.
        if mcp_thread is not None:
            mcp_thread.join(5)
        ui.messageBox('Fusion MCP Server add-in stopped.')
    except Exception as e:
        ui.messageBox(f'Error stopping add-in: {e}')
