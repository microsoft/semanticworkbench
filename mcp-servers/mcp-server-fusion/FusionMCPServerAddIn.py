import adsk.core
import adsk.fusion
import adsk.cam
import threading
import logging
import os
import tempfile

# Global flag to signal the MCP server thread to stop.
mcp_running = True
mcp_thread = None

def run(context):
    global mcp_running, mcp_thread
    app = adsk.core.Application.get()
    ui = app.userInterface
    try:
        # Set up logging with both file and stream handlers
        log_path = os.path.join(tempfile.gettempdir(), 'fusion_addin.log')
        logging.basicConfig(
            level=logging.DEBUG,
            format='%(asctime)s - %(levelname)s - %(message)s',
            handlers=[
                logging.FileHandler(log_path, mode='w'),
                logging.StreamHandler()  # This will print to system console
            ],
            force=True
        )
        
        ui.messageBox(f'Log file location: {log_path}')
        logging.info('Starting MCP Server add-in')
        
        # Start the background thread
        mcp_running = True
        mcp_thread = threading.Thread(target=start_mcp_server, daemon=True)
        mcp_thread.start()
        logging.info('Background thread started')
        
    except Exception as e:
        logging.error(f'Failed to start: {str(e)}', exc_info=True)
        ui.messageBox(f'Failed to start: {str(e)}')

def start_mcp_server():
    try:
        logging.info('MCP server thread initializing')
        from .mcp_server.server import create_mcp_server
        
        logging.info('Creating MCP server')
        mcp = create_mcp_server()
        
        logging.info('Configuring MCP server')
        mcp.settings.port = 6050
        
        logging.info(f'Starting MCP server on port {mcp.settings.port}')
        mcp.run(transport='sse')
        
    except Exception:
        logging.error('Error in MCP server thread', exc_info=True)
        # Don't use UI messages in the thread

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
