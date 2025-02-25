import adsk.core

from textwrap import dedent
from typing import List

from ..fusion_utils import (
    errorHandler,
    FusionContext,
    GeometryValidator,
)
from ..vendor.mcp.server.fastmcp import FastMCP


class FusionPatternTools:
    def __init__(self):
        self.ctx = FusionContext()
        self.validator = GeometryValidator()

    def register_tools(self, mcp: FastMCP):
        """
        Register tools with the MCP server.
        """

        @mcp.tool(
            name="rectangular_pattern",
            description=dedent("""
                Creates a rectangular (grid) pattern of existing entities in the Fusion 360 workspace.
        
                Arranges copies of the specified entities in a grid defined by the number of instances and spacing along the X and Y directions.
                The pattern is aligned using the root component's X and Y construction axes.
                
                Args:
                    entity_names (List[str]): A list of names corresponding to the entities (e.g., bodies) to be patterned. Each name must reference an existing entity.
                    xCount (int): The number of instances to create along the X direction.
                    xSpacing (float): The spacing distance between instances along the X axis.
                    yCount (int): The number of instances to create along the Y direction.
                    ySpacing (float): The spacing distance between instances along the Y axis.
                Returns:
                    List[str]: A list containing the names of the patterned entities.
            """).strip(),
        )
        @errorHandler
        def rectangular_pattern(
            entity_names: List[str], 
            xCount: int,
            xSpacing: float,
            yCount: int,
            ySpacing: float,
        ) -> List[str]:
            # Get the entities by name
            entities = [self.ctx.rootComp.bRepBodies.itemByName(name) for name in entity_names]
            
            # Create the pattern
            pattern = self.ctx.rootComp.features.rectangularPatternFeatures

            patternInput = pattern.createInput(entities, adsk.fusion.PatternDistanceType.SpacingPatternDistanceType)
            patternInput.directionOne = self.ctx.rootComp.xConstructionAxis
            patternInput.directionTwo = self.ctx.rootComp.yConstructionAxis
            patternInput.quantityOne = xCount
            patternInput.quantityTwo = yCount
            patternInput.spacingOne = adsk.core.ValueInput.createByReal(xSpacing)
            patternInput.spacingTwo = adsk.core.ValueInput.createByReal(ySpacing)

            pattern.add(patternInput)
            
            return [entity.name for entity in entities]
