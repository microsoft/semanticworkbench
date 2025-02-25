import adsk.core
import adsk.fusion

from textwrap import dedent

from ..fusion_utils import (
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
                Creates a new body by extruding a sketch profile.
        
                Ensure the sketch exists and contains a valid, closed profile. The extrusion is
                performed in the specified direction (defaulting to positive Z if omitted).
                
                Args:
                    sketch_name (str): Name of the sketch containing the profile. Must reference a valid, closed profile.
                    distance (float): Extrusion distance (positive value representing the length).
                    direction (list[float], optional): Extrusion direction as [x, y, z]. Defaults to positive Z.
                Returns:
                    str: The name of the newly created body.
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
                Creates a cut by extruding a sketch profile from an existing face.
                
                IMPORTANT: Ensure that the sketch is located on the face where the cut is intended.
                For features on the top face, create the sketch on an offset plane at the block's top (using create_sketch_on_offset_plane)
                and set the extrusion direction to [0, 0, -1] to cut downward.
                
                Args:
                    sketch_name (str): Name of the sketch containing the cut profile.
                    distance (float): The extrusion distance (set to at least the full thickness of the feature).
                    target_body_name (str): Name of the body to cut; must be an existing body.
                    direction (list[float], optional): The extrusion direction as [x, y, z]. Defaults to positive Z unless specified.
                Returns:
                    str: The name of the resulting body after the cut.
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

