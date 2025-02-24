import asyncio

from .vendor import anyio
from .vendor.mcp.server.fastmcp import FastMCP

from .mcp_tools import (
    Fusion3DOperationTools,
    FusionGeometryTools,
    FusionPatternTools,
    FusionSketchTools,
)

def custom_exception_handler(loop, context):
    """
    Custom exception handler for the event loop.
    Ignores certain exceptions that occur during normal client disconnects.
    """
    exception = context.get("exception")
    if isinstance(exception, (anyio.BrokenResourceError, anyio.WouldBlock, asyncio.CancelledError)):
        # These exceptions are expected during disconnections or cancellation.
        # You can log a warning if desired, or simply ignore.
        print("Warning (ignored):", exception)
    else:
        # For all other exceptions, use the default handler.
        loop.default_exception_handler(context)

class FusionMCPServer:
    def __init__(self, port: int):
        self.running = False
        self.mcp = FastMCP(name="Fusion MCP Server", log_level="DEBUG")
        self.mcp.settings.port = port

        # Register tools
        Fusion3DOperationTools().register_tools(self.mcp)
        FusionGeometryTools().register_tools(self.mcp)
        FusionPatternTools().register_tools(self.mcp)
        FusionSketchTools().register_tools(self.mcp)

    async def _run_server(self):
        try:
            await self.mcp.run_sse_async()
        except (asyncio.CancelledError, anyio.BrokenResourceError) as e:
            # This block might still be hit on shutdown, so we can ignore these exceptions.
            print("Server run cancelled or broken:", e)
        except Exception as e:
            # Re-raise unexpected exceptions.
            raise e

    def start(self):
        self.running = True
        self.loop = asyncio.new_event_loop()
        # Set the custom exception handler on this loop.
        self.loop.set_exception_handler(custom_exception_handler)
        asyncio.set_event_loop(self.loop)
        self.task = self.loop.create_task(self._run_server())
        try:
            self.loop.run_forever()
        except Exception as e:
            print("Exception in run_forever:", e)
        finally:
            self.loop.close()

    def shutdown(self):
        if self.loop and self.loop.is_running():
            self.task.cancel()
            try:
                self.loop.run_until_complete(self.task)
            except (asyncio.CancelledError, anyio.BrokenResourceError):
                pass
            self.loop.call_soon_threadsafe(self.loop.stop)
            self.running = False


# import asyncio
# import time
# import subprocess
# import re

# from .vendor.mcp.server.fastmcp import FastMCP
# from .mcp_tools import (
#     Fusion3DOperationTools,
#     FusionGeometryTools,
#     FusionPatternTools,
#     FusionSketchTools,
# )


# def kill_process_on_port(port):
#     # FIXME: End processes on port
#     return
#     try:
#         # Run netstat to get the list of active connections and listening ports
#         output = subprocess.check_output("netstat -ano", shell=True, text=True)
#         # Iterate over each line of the netstat output
#         for line in output.splitlines():
#             # Look for lines that contain the specified port and are in the LISTENING state
#             if re.search(rf":{port}\s+", line) and "LISTENING" in line:
#                 parts = line.split()
#                 pid = parts[-1]  # PID is the last element on the line
#                 # Forcefully kill the process using taskkill
#                 subprocess.run(f"taskkill /PID {pid} /F", shell=True)
#                 print(f"Killed process {pid} on port {port}")
#     except Exception as e:
#         print(f"Error killing process on port {port}: {e}")



# class FusionMCPServer:
#     def __init__(self, port: int):
#         self.running = False

#         # Initialize MCP server
#         self.mcp = FastMCP(name="Fusion MCP Server", log_level="DEBUG")
#         self.mcp.settings.port = port

#         # Register tools
#         Fusion3DOperationTools().register_tools(self.mcp)
#         FusionGeometryTools().register_tools(self.mcp)
#         FusionPatternTools().register_tools(self.mcp)
#         FusionSketchTools().register_tools(self.mcp)

#     async def cleanup(self):
#         # Perform any necessary cleanup here
#         pass

#     def start(self):
#         self.running = True
#         self.loop = asyncio.new_event_loop()
#         asyncio.set_event_loop(self.loop)
#         # Create a task for the uvicorn-based server
#         self.task = self.loop.create_task(self.mcp.run_sse_async())
#         try:
#             self.loop.run_forever()
#         except Exception as e:
#             print(f"Exception in server loop: {e}")
#         finally:
#             self.loop.close()

#     # Example shutdown method in your FusionMCPServer class:
#     def shutdown(self):
#         if self.loop and self.loop.is_running():
#             # Cancel the running uvicorn server task
#             self.task.cancel()
#             # Stop the event loop
#             self.loop.call_soon_threadsafe(self.loop.stop)
#             self.running = False
#             # Give a moment for shutdown to process
#             time.sleep(1)
#             # Kill any lingering process on the port
#             kill_process_on_port(self.mcp.settings.port)

