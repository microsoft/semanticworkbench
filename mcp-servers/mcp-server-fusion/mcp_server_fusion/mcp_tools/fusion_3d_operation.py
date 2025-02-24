import adsk.core
import adsk.fusion

from textwrap import dedent

from ..fusion_utils import (
    convert_direction,
    errorHandler,
    FusionContext,
    GeometryValidator,
)
from ..vendor.mcp.server.fastmcp import FastMCP


class Fusion3DOperationTools:
    def __init__(self):
        self.ctx = FusionContext()
        self.validator = GeometryValidator()

    def register_tools(self, mcp: FastMCP):
        """
        Register tools with the MCP server.
        """

        @mcp.tool(
            name="extrude",
            description=dedent("""
                Creates an extrusion from a sketch profile.
                               
                Args:
                    sketch_name (str): The name of the sketch containing the profile.
                    distance (float): The extrusion distance.
                    direction (list[float], optional): The extrusion direction (x,y,z). Defaults to None.
                Returns:
                    str: The created body name.
            """).strip(),
        )
        @errorHandler
        def extrude(
            sketch_name: str,
            distance: float,
            direction: list[float] = None
        ) -> str:
            # Get the sketch by name
            sketch = self.ctx.rootComp.sketches.itemByName(sketch_name)
            if not sketch:
                raise ValueError(f"Sketch '{sketch_name}' not found.")
            
            # Get the profile from sketch
            profile = sketch.profiles.item(0)
            
            # Create extrusion input
            extrudes = self.ctx.rootComp.features.extrudeFeatures
            distance_input = adsk.core.ValueInput.createByReal(distance)
            
            # Set up the extrusion
            extInput = extrudes.createInput(profile, adsk.fusion.FeatureOperations.NewBodyFeatureOperation)
            
            # Create a distance extent definition
            extent = adsk.fusion.DistanceExtentDefinition.create(distance_input)
            
            # Set the extent based on direction
            if direction and direction[2] < 0:
                extInput.setOneSideExtent(extent, adsk.fusion.ExtentDirections.NegativeExtentDirection)
            else:
                extInput.setOneSideExtent(extent, adsk.fusion.ExtentDirections.PositiveExtentDirection)
                
            # Create the extrusion
            ext = extrudes.add(extInput)
            return ext.bodies.item(0).name

        @mcp.tool(
            name="cut_extrude",
            description=dedent("""
                Creates a cut extrusion from a sketch profile.
                               
                Args:
                    sketch_name (str): The name of the sketch containing the profile.
                    distance (float): The extrusion distance.
                    target_body_name (str): The target body name.
                    direction (list[float], optional): The extrusion direction (x,y,z). Defaults to None.
                Returns:
                    str: The created body name.
            """).strip(),
        )
        @errorHandler
        def cut_extrude(
            sketch_name: str,
            distance: float,
            target_body_name: str,
            direction: list[float] = None
        ) -> str:
            # Get the sketch by name
            sketch = self.ctx.rootComp.sketches.itemByName(sketch_name)
            if not sketch:
                raise ValueError(f"Sketch '{sketch_name}' not found.")
            
            # Get the target body by name
            target_body = self.ctx.rootComp.bRepBodies.itemByName(target_body_name)
            if not target_body:
                raise ValueError(f"Target body '{target_body_name}' not found.")
            
            # Get the profile from sketch
            profile = sketch.profiles.item(0)

            # Create extrusion input
            extrudes = self.ctx.rootComp.features.extrudeFeatures
            distance_input = adsk.core.ValueInput.createByReal(distance)
            
            # Set up the extrusion
            extInput = extrudes.createInput(profile, adsk.fusion.FeatureOperations.CutFeatureOperation)
            
            # Create a distance extent definition
            extent = adsk.fusion.DistanceExtentDefinition.create(distance_input)
            
            # Set the extent based on direction
            if direction and direction[2] < 0:
                extInput.setOneSideExtent(extent, adsk.fusion.ExtentDirections.NegativeExtentDirection)
            else:
                extInput.setOneSideExtent(extent, adsk.fusion.ExtentDirections.PositiveExtentDirection)
            
            # Add the target body to participants
            extInput.participantBodies = [target_body]
            
            # Create the extrusion
            ext = extrudes.add(extInput)
            return ext.bodies.item(0).name

