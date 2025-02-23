import asyncio

from ..vendor.mcp.server.fastmcp import FastMCP

from .. import fusion_utils

from . import settings


# Set the name of the MCP server
server_name = "Fusion MCP Server"


async def run_tool_async(
    tool_func, *args, **kwargs
) -> str:
    """
    Runs a tool function asynchronously.

    Args:
        tool_func (function): The tool function to run.
        *args: Positional arguments for the tool function.
        **kwargs: Keyword arguments for the tool function.

    Returns:
        str: Result of the tool function.
    """

    try:
        fusion_utils.log(f"Running tool: {tool_func.__name__}, args: {args}, kwargs: {kwargs}")
        result = await asyncio.to_thread(tool_func, *args, **kwargs)

        fusion_utils.log(f"Tool result: {result}")
        return result
    
    except Exception as e:
        fusion_utils.handle_error(tool_func.__name__, settings.show_errors_in_ui)
        fusion_utils.log(f"Error in tool {tool_func.__name__}: {str(e)}")
        raise


def create_mcp_server() -> FastMCP:

    # Initialize FastMCP with debug logging.
    mcp = FastMCP(name=server_name, log_level=settings.log_level)

    # Import and register tools
    from .tools import (
        create_sketch_tool,
        add_geometry_to_sketch_tool,
        extrude_profile_tool,
        list_design_elements_tool,
        measure_feature_tool
    )

    @mcp.tool()
    async def create_sketch(
        plane: str,
        sketch_name: str = None
    ) -> str:
        """
        Creates a new sketch on the specified plane.

        Args:
            plane (str): The plane on which to create the sketch (XY, XZ, or YZ).
            sketch_name (str, optional): Optional name for the sketch. Defaults to None.
        Returns:
            str: Success or error message.
        """
        return await run_tool_async(
            tool_func=create_sketch_tool,
            plane=plane,
            sketch_name=sketch_name
        )

    @mcp.tool()
    async def add_geometry_to_sketch(
        sketch_id: str,
        geometry: dict
    ) -> str:
        """
        Adds geometry to an existing sketch.

        For rectangles, provide 'corner1' and 'corner2' as [x, y] arrays.
        For circles, provide 'center' as [x, y] and 'radius'.

        Example:
        {
            'type': 'rectangle',
            'corner1': [0, 0],
            'corner2': [10, 5]
        }
        or
        {
            'type': 'circle',
            'center': [5, 5],
            'radius': 3
        }

        Args:
            sketch_id (str): The identifier of the target sketch.
            geometry (dict): Geometry details.
        Returns:
            str: Success or error message.        
        """
        return await run_tool_async(
            tool_func=add_geometry_to_sketch_tool,
            sketch_id=sketch_id,
            geometry=geometry
        )

    @mcp.tool()
    async def extrude_profile(
        sketch_id: str,
        profile_index: int,
        distance: float,
        operation: str
    ) -> str:
        """
        Extrudes a closed profile from a sketch to create or modify a 3D feature.

        Args:
            sketch_id (str): The identifier of the sketch containing the profile.
            profile_index (int): The index of the profile in the sketch to extrude.
            distance (float): Extrusion distance (positive = join).
            operation (str): Type of operation ('join', 'cut', or 'newBody').
        Returns:
            str: Success or error message.
        """
        return await run_tool_async(
            tool_func=extrude_profile_tool, 
            sketch_id=sketch_id,
            profile_index=profile_index,
            distance=distance,
            operation=operation
        )
    
    @mcp.tool()
    async def list_design_elements() -> dict:
        """
        Lists key design elements such as sketches and bodies.
        
        Returns:
            dict: Dictionary containing lists of sketches and bodies.
        """
        return await run_tool_async(
            tool_func=list_design_elements_tool
        )

    @mcp.tool()
    async def measure_feature(
        object_id: str
    ) -> dict:
        """
        Measures a given feature in the design.

        Args:
            object_id (str): ID of the target object.
        Returns:
            dict: Measurement results.
        """
        return await run_tool_async(
            tool_func=measure_feature_tool,
            object_id=object_id
        )

    return mcp
