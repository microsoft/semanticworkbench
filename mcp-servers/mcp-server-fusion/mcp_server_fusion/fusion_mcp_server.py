import asyncio
import logging
from contextlib import suppress
from typing import Optional
import threading
import socket
import time

from .vendor.mcp.server.fastmcp import FastMCP
from .vendor.anyio import BrokenResourceError
from .mcp_tools import (
    Fusion3DOperationTools,
    FusionGeometryTools,
    FusionPatternTools,
    FusionSketchTools,
)

class FusionMCPServer:
    def __init__(self, port: int):
        self.port = port
        self.running = False
        self.loop: Optional[asyncio.AbstractEventLoop] = None
        self.shutdown_event = threading.Event()
        self.server_task: Optional[asyncio.Task] = None
        self.logger = logging.getLogger(__name__)
        
        # Initialize MCP server
        self.mcp = FastMCP(name="Fusion MCP Server", log_level="DEBUG")
        self.mcp.settings.port = port
        
        # Register tools
        self._register_tools()

    def wait_for_port_available(self, timeout=30):
        """Wait for the port to become available"""
        start_time = time.time()
        while time.time() - start_time < timeout:
            try:
                # Try to bind to the port
                with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
                    s.bind(('0.0.0.0', self.port))
                    return True
            except OSError:
                time.sleep(0.5)
        return False

    async def _keep_loop_running(self):
        """Keep the event loop running"""
        while not self.shutdown_event.is_set():
            await asyncio.sleep(0.1)

    def _register_tools(self):
        """Register all tool handlers"""
        try:
            Fusion3DOperationTools().register_tools(self.mcp)
            FusionGeometryTools().register_tools(self.mcp)
            FusionPatternTools().register_tools(self.mcp)
            FusionSketchTools().register_tools(self.mcp)
        except Exception as e:
            self.logger.error(f"Error registering tools: {e}")
            raise

    async def _run_server(self):
        """Run the server"""
        try:
            self.running = True
            
            # Create task for server
            server_task = asyncio.create_task(self.mcp.run_sse_async())
            keep_alive_task = asyncio.create_task(self._keep_loop_running())
            
            # Wait for either task to complete
            done, pending = await asyncio.wait(
                [server_task, keep_alive_task],
                return_when=asyncio.FIRST_COMPLETED
            )
            
            # Cancel remaining tasks
            for task in pending:
                task.cancel()
                with suppress(asyncio.CancelledError):
                    await task
            
        except asyncio.CancelledError:
            self.logger.info("Server cancelled, shutting down...")
        except Exception as e:
            self.logger.error(f"Server error: {e}")
            raise
        finally:
            self.running = False

    def start(self):
        """Start the server in the current thread"""
        if self.running:
            return

        try:
            # Wait for port to become available
            if not self.wait_for_port_available():
                raise RuntimeError(f"Port {self.port} did not become available")

            # Create new event loop
            self.loop = asyncio.new_event_loop()
            asyncio.set_event_loop(self.loop)
            
            # Set up exception handler
            def handle_exception(loop, context):
                exception = context.get('exception')
                if isinstance(exception, (asyncio.CancelledError, GeneratorExit)):
                    return
                self.logger.error(f"Caught unhandled exception: {context}")
                if not self.shutdown_event.is_set():
                    self.shutdown()
            
            self.loop.set_exception_handler(handle_exception)
            
            # Run the server
            try:
                self.running = True
                self.server_task = asyncio.ensure_future(self._run_server(), loop=self.loop)
                self.loop.run_forever()
            except BrokenResourceError:
                self.logger.warning("Client disconnected during SSE, ignoring BrokenResourceError")
            except KeyboardInterrupt:
                pass
            except Exception as e:
                if not self.shutdown_event.is_set():  # Don't log during normal shutdown
                    self.logger.error(f"Error in server loop: {e}")
            finally:
                self._cleanup()
                
        except Exception as e:
            self.logger.error(f"Error starting server: {e}")
            raise

    def _cleanup(self):
        """Clean up resources"""
        try:
            if self.loop and self.loop.is_running():
                # Cancel all tasks
                tasks = [t for t in asyncio.all_tasks(self.loop) if not t.done()]
                
                if tasks:
                    # Cancel tasks
                    for task in tasks:
                        task.cancel()
                    
                    # Wait for tasks to finish with timeout
                    try:
                        self.loop.run_until_complete(
                            asyncio.wait(tasks, timeout=5)
                        )
                    except Exception:
                        pass
            
            # Close the loop
            if self.loop and not self.loop.is_closed():
                self.loop.close()
            
            # Ensure socket is closed properly
            try:
                with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
                    s.settimeout(1)
                    s.connect(('127.0.0.1', self.port))
                    s.close()
            except Exception:
                pass
            
            self.running = False
            
        except Exception as e:
            self.logger.error(f"Error during cleanup: {e}")

    def shutdown(self):
        """Shutdown the server safely"""
        if not self.running:
            return

        try:
            self.logger.info("Shutting down server...")
            self.shutdown_event.set()
            self.running = False
            
            if self.loop and self.loop.is_running():
                def stop_loop():
                    # Stop the loop
                    self.loop.stop()
                    # Cancel any pending tasks
                    for task in asyncio.all_tasks(self.loop):
                        task.cancel()
                
                self.loop.call_soon_threadsafe(stop_loop)
            
        except Exception as e:
            self.logger.error(f"Error during shutdown: {e}")
            raise
