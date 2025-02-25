import adsk.core

from textwrap import dedent

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
                Creates a line between two 3D points.
        
                Draws a line connecting the specified start and end points. If a sketch name is provided,
                the line is created in that sketch; otherwise, a construction line is added to the root component.
                
                Args:
                    start_point (list[float]): A list [x, y, z] representing the starting point.
                    end_point (list[float]): A list [x, y, z] representing the ending point.
                    sketch_name (str, optional): The name of the sketch to draw the line. Defaults to None.
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
                Creates a circle given a center and radius.
        
                Draws a circle centered at the specified point with the provided radius. If a sketch name is provided,
                the circle is added to that sketch; otherwise, it is added as a construction circle in the root component.
                
                Args:
                    center (list[float]): A list [x, y, z] representing the circle's center.
                    radius (float): The radius of the circle (positive value).
                    sketch_name (str, optional): The name of the sketch to create the circle. Defaults to None.
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
                Creates a rectangle defined by two diagonal corner points.
        
                Draws a rectangle between two specified 3D points. If a sketch name is provided,
                the rectangle is created within that sketch; otherwise, it is created as construction lines in the root component.
                
                Args:
                    point_1 (list[float]): A list [x, y, z] representing the first corner.
                    point_2 (list[float]): A list [x, y, z] representing the opposite corner.
                    sketch_name (str, optional): The name of the sketch to create the rectangle. Defaults to None.
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
