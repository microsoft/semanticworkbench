import atexit
import threading
import signal
import logging

from .mcp_server_fusion.fusion_mcp_server import FusionMCPServer
from .mcp_server_fusion.fusion_utils import log, handle_error

class FusionMCPAddIn:
    def __init__(self, port: int = 6050, show_errors: bool = True):
        self.port = port
        self.show_errors = show_errors
        self.server = None
        self.server_thread = None
        self.shutdown_event = threading.Event()
        self.logger = logging.getLogger(__name__)

    def start(self):
        """Start the MCP server in a background thread"""
        if self.server_thread and self.server_thread.is_alive():
            return
            
        try:
            log('Starting MCP Server add-in')
            
            # Create server instance
            self.server = FusionMCPServer(self.port)
            
            # Start server in background thread
            self.server_thread = threading.Thread(
                target=self._run_server,
                daemon=True,
                name="MCPServerThread"
            )
            self.server_thread.start()
            
            # Set up signal handlers
            signal.signal(signal.SIGTERM, lambda sig, frame: self.stop())
            atexit.register(self.stop)
            
            log('MCP Server add-in started successfully')
            
        except Exception as e:
            handle_error('start', self.show_errors)
            self.logger.error(f'Failed to start add-in: {str(e)}')
            self.stop()

    def _run_server(self):
        """Run the server in the background thread"""
        try:
            log('Starting MCP server thread')
            if self.server:
                self.server.start()
            log('MCP server thread stopping')
            
        except Exception as e:
            if not self.shutdown_event.is_set():
                handle_error('_run_server', self.show_errors)
                self.logger.error(f'Error in server thread: {str(e)}')
        finally:
            self.shutdown_event.set()

    def stop(self):
        """Stop the MCP server and clean up resources"""
        if self.shutdown_event.is_set():
            return
            
        try:
            log('Stopping MCP Server add-in')
            self.shutdown_event.set()
            
            # Stop server
            if self.server:
                self.server.shutdown()
                self.server = None
                log('MCP server stopped')
            
            # Wait for thread to finish
            if self.server_thread and self.server_thread.is_alive():
                self.server_thread.join(timeout=5)
                self.server_thread = None
                log('Server thread stopped')
            
            log('MCP Server add-in stopped')
            
        except Exception as e:
            handle_error('stop', self.show_errors)
            self.logger.error(f'Error stopping add-in: {str(e)}')

# Global add-in instance
_addin = None

def run(context):
    """Add-in entry point"""
    global _addin
    if _addin is None:
        _addin = FusionMCPAddIn()
        _addin.start()

def stop(context):
    """Add-in cleanup point"""
    global _addin
    if _addin is not None:
        _addin.stop()
        _addin = None
