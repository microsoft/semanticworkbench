import adsk.core

# Tool: Extrude Profile
def extrude_profile_tool(sketch_id: str, profile_index: int, distance: float, operation: str) -> str:
    """Extrudes a closed profile from a sketch to create or modify a 3D feature."""
    app = adsk.core.Application.get()

    try:
        design = app.activeProduct
        if not isinstance(design, adsk.fusion.Design):
            return "No active Fusion design found."

        rootComp = design.rootComponent
        sketch = rootComp.sketches.itemByName(sketch_id)
        if not sketch:
            return f"Sketch with id '{sketch_id}' not found."

        profile = sketch.profiles[profile_index]
        if not profile:
            return f"Profile with index {profile_index} not found in sketch '{sketch_id}'."

        extrudes = rootComp.features.extrudeFeatures
        distance_value = adsk.core.ValueInput.createByReal(distance)

        if operation == 'join':
            operation_type = adsk.fusion.FeatureOperations.JoinFeatureOperation
        elif operation == 'cut':
            operation_type = adsk.fusion.FeatureOperations.CutFeatureOperation
        elif operation == 'newBody':
            operation_type = adsk.fusion.FeatureOperations.NewBodyFeatureOperation
        else:
            return "Invalid operation type. Choose 'join', 'cut', or 'newBody'."

        extrude_input = extrudes.createInput(profile, operation_type)
        extrude_input.setDistanceExtent(False, distance_value)
        extrudes.add(extrude_input)

        return "Profile extruded successfully."
    except Exception as e:
        return f"Error extruding profile: {e}"
