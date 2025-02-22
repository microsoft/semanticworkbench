from mcp.server.fastmcp import FastMCP
import adsk.core


from . import settings

# Set the name of the MCP server
server_name = "Fusion MCP Server"

def create_mcp_server() -> FastMCP:

    # Initialize FastMCP with debug logging.
    mcp = FastMCP(name=server_name, log_level=settings.log_level)

    # Define each tool and its setup.

    # Fusion 360 Specific Tool - Create a Rectangle
    @mcp.tool()
    async def create_rectangle(x1: float, y1: float, x2: float, y2: float) -> str:
        """Creates a rectangle on the XY plane in the open Fusion design.

        Parameters:
          x1, y1 - bottom-left coordinates
          x2, y2 - top-right coordinates
        """
        # Get the Fusion 360 application and active design.
        app = adsk.core.Application.get()
        ui = app.userInterface
        try:
            design = app.activeProduct
            rootComp = design.rootComponent
            sketches = rootComp.sketches
            xyPlane = rootComp.xYConstructionPlane
            sketch = sketches.add(xyPlane)
            lines = sketch.sketchCurves.sketchLines
            lines.addTwoPointRectangle(adsk.core.Point3D.create(x1, y1, 0),
                                       adsk.core.Point3D.create(x2, y2, 0))
            return "Rectangle created successfully."
        except Exception as e:
            return f"Error creating rectangle: {e}"
    return mcp
