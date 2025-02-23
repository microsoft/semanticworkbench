import adsk.core

# Tool: Create Sketch
def create_sketch_tool(plane: str, sketch_name: str = None) -> str:
    """Creates a new sketch on a specified plane."""
    app = adsk.core.Application.get()

    try:
        design = app.activeProduct
        if not isinstance(design, adsk.fusion.Design):
            return "No active Fusion design found."

        rootComp = design.rootComponent
        if plane == 'XY':
            selected_plane = rootComp.xYConstructionPlane
        elif plane == 'XZ':
            selected_plane = rootComp.xZConstructionPlane
        elif plane == 'YZ':
            selected_plane = rootComp.yZConstructionPlane
        else:
            return "Invalid plane specified. Choose XY, XZ, or YZ."

        sketch = rootComp.sketches.add(selected_plane)
        if sketch_name:
            sketch.name = sketch_name

        return f"Sketch '{sketch.name}' created successfully."
    except Exception as e:
        return f"Error creating sketch: {e}"

# Tool: Add Geometry to Sketch
def add_geometry_to_sketch_tool(sketch_id: str, geometry: dict) -> str:
    """Adds geometry to an existing sketch."""
    app = adsk.core.Application.get()

    try:
        design = app.activeProduct
        if not isinstance(design, adsk.fusion.Design):
            return "No active Fusion design found."

        rootComp = design.rootComponent
        sketch = rootComp.sketches.itemByName(sketch_id)
        if not sketch:
            return f"Sketch with id '{sketch_id}' not found."

        sketch_curves = sketch.sketchCurves
        if geometry['type'] == 'rectangle':
            p1 = adsk.core.Point3D.create(geometry['corner1'][0], geometry['corner1'][1], 0)
            p2 = adsk.core.Point3D.create(geometry['corner2'][0], geometry['corner2'][1], 0)
            sketch_curves.sketchLines.addTwoPointRectangle(p1, p2)
        elif geometry['type'] == 'circle':
            center = adsk.core.Point3D.create(geometry['center'][0], geometry['center'][1], 0)
            radius = geometry['radius']
            sketch_curves.sketchCircles.addByCenterRadius(center, radius)
        else:
            return "Unsupported geometry type. Supported types are 'rectangle' and 'circle'."

        return "Geometry added successfully."
    except Exception as e:
        return f"Error adding geometry to sketch: {e}"