import atexit
import threading
import signal

from .mcp_server_fusion.fusion_mcp_server import FusionMCPServer
from .mcp_server_fusion.fusion_utils import log, handle_error


# Global variables
mcp_running = True
mcp_thread = None
fusion_mcp_server = None
show_errors_in_ui = True


def run(context):
    global mcp_running, mcp_thread

    try:
        log('Starting MCP Server add-in')
        
        # Start the background thread
        log('Starting background thread')
        mcp_running = True
        mcp_thread = threading.Thread(target=start_mcp_server, daemon=True)
        mcp_thread.start()
        log('Background thread started')

        atexit.register(stop, None)
        signal.signal(signal.SIGTERM, lambda sig, frame: stop(None))

        
    except Exception as e:
        handle_error('run', show_errors_in_ui)
        log(f'Failed to start: {str(e)}')


def start_mcp_server(port: int = 6050):
    global fusion_mcp_server

    try:
        log('Creating MCP server')
        fusion_mcp_server = FusionMCPServer(port)

        log(f'Starting MCP server on port {port}')
        fusion_mcp_server.start()
        log('MCP server thread started')
        
    except Exception as e:
        handle_error('start_mcp_server', show_errors_in_ui)
        log(f'Error in MCP server thread: {str(e)}')


def stop(context):
    global mcp_running, mcp_thread, fusion_mcp_server

    try:
        log('Stopping MCP Server add-in')

        # Signal the background thread to stop
        mcp_running = False
        log('Signaling background thread to stop')

        if fusion_mcp_server is not None:
            fusion_mcp_server.shutdown()
            log('MCP server stopped')
        else:
            log('No MCP server to stop')
        
        # Stop the thread
        if mcp_thread is not None:
            mcp_thread.join(5)
            log('Background thread stopped')
        else:
            log('No background thread to stop')
            
        log('MCP Server add-in stopped')
        
    except Exception as e:
        handle_error('stop', show_errors_in_ui)
        log(f'Error stopping add-in: {str(e)}')
