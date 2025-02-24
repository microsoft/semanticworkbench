from textwrap import dedent

from ..fusion_utils import (
    errorHandler,
    FusionContext,
    GeometryValidator,
    get_sketch_by_name,
)
from ..vendor.mcp.server.fastmcp import FastMCP

class FusionSketchTools:
    def __init__(self):
        self.ctx = FusionContext()
        self.validator = GeometryValidator()

    def register_tools(self, mcp: FastMCP):
        """
        Register tools with the MCP server.
        """
        
        @mcp.tool(
            name="sketches",
            description=dedent("""
                Returns the names of all sketches in the root component.
                
                Returns:
                    list[str]: List of sketch names.
            """).strip(),
        )
        @errorHandler
        def sketches() -> list[str]:
            # Get all sketches in the root component
            sketches = self.ctx.rootComp.sketches
            return [sketch.name for sketch in sketches]

        @mcp.tool(
            name="create_sketch",
            description=dedent("""
                Creates a new sketch on the specified plane.
                
                Args:
                    plane (str): The plane to create the sketch on, e.g., "XY", "XZ", "YZ".
                    sketch_name (str, optional): The name of the sketch. Defaults to None.
                Returns:
                    str: The created sketch name.
            """).strip(),
        )
        @errorHandler
        def create_sketch(
            plane: str,
            sketch_name: str = None,    
        ) -> str:
            # Create a new sketch on the specified plane
            sketches = self.ctx.rootComp.sketches
            
            if plane == "XY":
                plane = self.ctx.rootComp.xYConstructionPlane
            elif plane == "XZ":
                plane = self.ctx.rootComp.xZConstructionPlane
            elif plane == "YZ":
                plane = self.ctx.rootComp.yZConstructionPlane
            else:
                raise ValueError("Invalid plane specified.")
            
            # Create the sketch
            sketch = sketches.add(plane)
            if sketch_name:
                sketch.name = sketch_name
            return sketch.name
        
        @mcp.tool(
            name="project_to_sketch",
            description=dedent("""
                Projects an entity to the active sketch.
                Args:
                    entity_name (str): The name of the entity to project.
                    sketch_name (str): The name of the sketch to project to.
                Returns:
                    str: The name of the projected entity.
            """).strip(),
        )
        @errorHandler
        def project_to_sketch(
            entity_name: str,
            sketch_name: str,
        ) -> str:
            # Get the active sketch and entity
            sketch = get_sketch_by_name(sketch_name)
            if not sketch:
                raise ValueError(f"Sketch '{sketch_name}' not found.")
            
            entity = self.ctx.rootComp.bRepBodies.itemByName(entity_name)
            if not entity:
                raise ValueError(f"Entity '{entity_name}' not found.")
            
            # Project the entity to the sketch
            projected_entity = sketch.project(entity)
            return projected_entity.name
