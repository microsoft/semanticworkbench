import atexit
import threading
import signal

from .mcp_server_fusion.mcp_server.server import create_mcp_server
from .mcp_server_fusion import fusion_utils


# Global variables
mcp_running = True
mcp_thread = None
show_errors_in_ui = True


def run(context):
    global mcp_running, mcp_thread

    try:
        fusion_utils.log('Starting MCP Server add-in', force_console=True)
        
        # Start the background thread
        mcp_running = True
        mcp_thread = threading.Thread(target=start_mcp_server, daemon=True)
        mcp_thread.start()
        fusion_utils.log('Background thread started')

        atexit.register(stop, None)
        signal.signal(signal.SIGTERM, lambda sig, frame: stop(None))

        
    except Exception as e:
        fusion_utils.handle_error('run', show_errors_in_ui)
        fusion_utils.log(f'Failed to start: {str(e)}')


def start_mcp_server():
    try:
        fusion_utils.log('MCP server thread initializing')
        
        fusion_utils.log('Creating MCP server')
        mcp = create_mcp_server()
        
        fusion_utils.log('Configuring MCP server')
        mcp.settings.port = 6050
        
        fusion_utils.log(f'Starting MCP server on port {mcp.settings.port}')
        mcp.run(transport='sse')
        
    except Exception as e:
        fusion_utils.handle_error('start_mcp_server', show_errors_in_ui)
        fusion_utils.log(f'Error in MCP server thread: {str(e)}')


def stop(context):
    global mcp_running, mcp_thread, queue_listener
    # app = adsk.core.Application.get()
    # ui = app.userInterface
    try:
        # Remove all of the event handlers your app has created
        fusion_utils.clear_handlers()

        # Signal the background thread to stop
        mcp_running = False
        fusion_utils.log('Stopping MCP Server add-in')
        
        # Stop the thread
        if mcp_thread is not None:
            mcp_thread.join(5)
            
        fusion_utils.log('MCP Server add-in stopped')
        
    except Exception as e:
        fusion_utils.handle_error('stop', show_errors_in_ui)
        fusion_utils.log(f'Error stopping add-in: {str(e)}')
