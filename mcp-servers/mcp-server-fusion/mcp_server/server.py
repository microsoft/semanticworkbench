
from textwrap import dedent
from typing import Annotated

from ..vendor.mcp.server.fastmcp import FastMCP
from ..vendor.pydantic import Field

from . import settings

# Set the name of the MCP server
server_name = "Fusion MCP Server"

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

    @mcp.tool(
        name="create_sketch_tool",
        description="Creates a new sketch on a specified plane."
    )
    async def create_sketch(
        plane: Annotated[
            str,
            Field(description="The plane on which to create the sketch (XY, XZ, or YZ).")
        ],
        sketch_name: Annotated[
            str,
            Field(description="Optional name for the sketch (default: None).", default=None)
        ] = None
    ) -> str:
        return create_sketch_tool(plane, sketch_name)

    @mcp.tool(
        name="add_geometry_to_sketch_tool",
        description="Adds geometry to an existing sketch."
    )
    async def add_geometry_to_sketch(
        sketch_id: Annotated[
            str,
            Field(description="The identifier of the target sketch.")
        ],
        geometry: Annotated[
            dict,
            Field(description=dedent("""
                A dictionary describing the type ('rectangle', 'circle') and parameters.
                Use arrays for coordinates.
                For example:
                {
                    'type': 'rectangle',
                    'corner1': [x1, y1],
                    'corner2': [x2, y2]
                }
                or
                {
                    'type': 'circle',
                    'center': [xc, yc],
                    'radius': r
                }
            """))
        ]
    ) -> str:
        return add_geometry_to_sketch_tool(sketch_id, geometry)

    @mcp.tool(
        name="extrude_profile_tool",
        description="Extrudes a closed profile from a sketch to create or modify a 3D feature."
    )
    async def extrude_profile(
        sketch_id: Annotated[
            str,
            Field(description="The identifier of the sketch containing the profile.")
        ],
        profile_index: Annotated[
            int,
            Field(description="The index of the profile in the sketch to extrude.")
        ],
        distance: Annotated[
            float,
            Field(description="Extrusion distance (positive = join).")
        ],
        operation: Annotated[
            str,
            Field(description="Type of operation ('join', 'cut', or 'newBody').")
        ]
    ) -> str:
        return extrude_profile_tool(sketch_id, profile_index, distance, operation)
    
    @mcp.tool(
        name="list_design_elements_tool",
        description="Lists key design elements such as sketches and bodies."
    )
    async def list_design_elements() -> dict:
        return list_design_elements_tool()

    @mcp.tool(
        name="measure_feature_tool",
        description="Measures a given feature in the design."
    )
    async def measure_feature(
        object_id: Annotated[
            str,
            Field(description="ID of the target object.")
        ]
    ) -> dict:
        return measure_feature_tool(object_id)

    return mcp
