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
                Creates a rectangular pattern of entities in the Fusion 360 workspace.
                
                Args:
                    entity_names (List[str]): List of entity names to be patterned.
                    xCount (int): Number of instances in the X direction.
                    xSpacing (float): Spacing between instances in the X direction.
                    yCount (int): Number of instances in the Y direction.
                    ySpacing (float): Spacing between instances in the Y direction.
                Returns:
                    List[str]: List of patterned entity names.
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
