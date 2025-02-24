import adsk.core

from textwrap import dedent
from typing import List

from ..fusion_utils import (
    errorHandler,
    FusionContext,
    GeometryValidator,
    get_sketch_by_name,
)
from ..vendor.mcp.server.fastmcp import FastMCP


class FusionGeometryTools:
    def __init__(self):
        self.ctx = FusionContext()
        self.validator = GeometryValidator()

    def register_tools(self, mcp: FastMCP):
        """
        Register tools with the MCP server.
        """

        @mcp.tool(
            name="create_line",
            description=dedent("""
                Creates a line between two points.
                
                Args:
                    start_point (list[float]): Start point of the line, e.g., [x, y, z].
                    end_point (list[float]): End point of the line, e.g., [x, y, z].
                    sketch_name (str, optional): The name of the sketch to create the line in. Defaults to None.
                Returns:
                    bool: True if the line was created successfully.
            """).strip(),
        )
        @errorHandler
        def createLine(
            start_point: list[float],
            end_point: list[float],
            sketch_name: str = None
        ) -> bool:
            # Convert to adsk.core.Point3D
            self.validator.validatePoint(start_point)
            self.validator.validatePoint(end_point)
            start_point = adsk.core.Point3D.create(*start_point)
            end_point = adsk.core.Point3D.create(*end_point)

            # Create the line
            sketch = get_sketch_by_name(sketch_name)
            if sketch:
                sketch_lines = sketch.sketchCurves.sketchLines
                sketch_lines.addByTwoPoints(start_point, end_point)
            else:
                self.ctx.rootComp.constructionLines.addByTwoPoints(start_point, end_point)
            return True

        @mcp.tool(
            name="create_circle",
            description=dedent("""
                Creates a circle.
                
                Args:
                    center (list[float]): Center point of the circle, e.g., [x, y, z].
                    radius (float): Radius of the circle.
                    sketch_name (str, optional): The name of the sketch to create the circle in. Defaults to None.
                Returns:
                    bool: True if the circle was created successfully.
            """).strip(),
        )
        @errorHandler
        def createCircle(
            center: list[float],
            radius: float,
            sketch_name: str = None
        ) -> bool:
            # Convert to adsk.core.Point3D
            self.validator.validatePoint(center)
            center = adsk.core.Point3D.create(*center)

            # Create the circle
            sketch = get_sketch_by_name(sketch_name)
            if sketch:
                sketch_circles = sketch.sketchCurves.sketchCircles
                sketch_circles.addByCenterRadius(center, radius)
            else:
                self.ctx.rootComp.constructionCircles.addByCenterRadius(center, radius)
            return True
        
        @mcp.tool(
            name="create_rectangle",
            description=dedent("""
                Creates a rectangle between two points.
                
                Args:
                    point_1 (list[float]): First point of the rectangle, e.g., [x, y, z].
                    point_2 (list[float]): Second point of the rectangle, e.g., [x, y, z].
                    sketch_name (str, optional): The name of the sketch to create the rectangle in. Defaults to None.
                Returns:
                    bool: True if the rectangle was created successfully.
            """).strip(),
        )
        @errorHandler
        def createRectangle(
            point_1: list[float],
            point_2: list[float],
            sketch_name: str = None
        ) -> bool:
            # Convert to adsk.core.Point3D
            self.validator.validatePoint(point_1)
            self.validator.validatePoint(point_2)
            point_1 = adsk.core.Point3D.create(*point_1)
            point_2 = adsk.core.Point3D.create(*point_2)

            # Create the rectangle
            sketch = get_sketch_by_name(sketch_name)
            if sketch:
                sketch_lines = sketch.sketchCurves.sketchLines
                sketch_lines.addTwoPointRectangle(point_1, point_2)
            else:
                sketch_lines = self.ctx.rootComp.constructionLines.addTwoPointRectangle(point_1, point_2)
            return True
