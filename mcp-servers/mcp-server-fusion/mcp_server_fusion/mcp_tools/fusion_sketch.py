import adsk.core

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
                Retrieves the names of all sketches in the root component.
                
                Useful for referencing existing sketches in subsequent operations.
                
                Returns:
                    list[str]: A list containing the names of all sketches.
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
                Creates a new sketch on a specified base plane.
                
                The sketch is created on one of the primary construction planes ("XY", "XZ", or "YZ").
                Optionally, a name can be assigned to the new sketch.
                
                Args:
                    plane (str): The base plane to create the sketch on ("XY", "XZ", or "YZ").
                    sketch_name (str, optional): The name to assign to the new sketch. Defaults to None.
                Returns:
                    str: The name of the created sketch.
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
            name="create_sketch_on_offset_plane",
            description=dedent("""
                Creates a new sketch on a plane offset from a specified base plane.
                
                Use this tool when you need to create a sketch on a surface that isn’t at Z=0.
                For example, to add features on the top face of a block, set the offset_value to the block's height.
                
                Args:
                    base_plane (str): The base plane to offset from ("XY", "XZ", or "YZ").
                    offset_value (float): The distance to offset from the base plane (e.g., the block height for the top face).
                    sketch_name (str, optional): The name to assign to the new sketch. Defaults to None.
                Returns:
                    str: The name of the created sketch.
            """).strip(),
        )
        @errorHandler
        def create_sketch_on_offset_plane(
            base_plane: str,
            offset_value: float,
            sketch_name: str = None
        ) -> str:
            # Access the sketches and construction planes collections.
            sketches = self.ctx.rootComp.sketches
            constructionPlanes = self.ctx.rootComp.constructionPlanes
            
            # Select the base construction plane.
            if base_plane == "XY":
                base = self.ctx.rootComp.xYConstructionPlane
            elif base_plane == "XZ":
                base = self.ctx.rootComp.xZConstructionPlane
            elif base_plane == "YZ":
                base = self.ctx.rootComp.yZConstructionPlane
            else:
                raise ValueError("Invalid plane specified.")
            
            # Create a construction plane input and set it by offset from the selected base plane.
            planeInput = constructionPlanes.createInput()
            offsetVal = adsk.core.ValueInput.createByReal(offset_value)
            planeInput.setByOffset(base, offsetVal)
            
            # Add the new offset plane.
            offsetPlane = constructionPlanes.add(planeInput)
            
            # Create the sketch on the new offset plane.
            sketch = sketches.add(offsetPlane)
            if sketch_name:
                sketch.name = sketch_name
            return sketch.name
        
        @mcp.tool(
            name="project_to_sketch",
            description=dedent("""
                Projects an existing entity onto a specified sketch.
                
                The tool projects the geometry of an existing entity (e.g., a body) onto the target sketch,
                creating reference geometry for further modeling operations.
                
                Args:
                    entity_name (str): The name of the entity to project. Must reference an existing entity.
                    sketch_name (str): The name of the sketch to project onto. The sketch must exist.
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
