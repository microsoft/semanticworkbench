import adsk.core
import adsk.fusion
from functools import wraps


class FusionContext:
    """Utility class to manage Fusion 360 application context"""
    
    @property
    def app(self) -> adsk.core.Application:
        return adsk.core.Application.get()
    
    @property
    def design(self) -> adsk.fusion.Design:
        if not self.app.activeProduct:
            raise RuntimeError('No active product')
        if not isinstance(self.app.activeProduct, adsk.fusion.Design):
            raise RuntimeError('Active product is not a Fusion design')

        return self.app.activeProduct
        
    @property
    def rootComp(self) -> adsk.fusion.Component:
        return self.design.rootComponent
    
    @property
    def fusionUnitsManager(self) -> adsk.fusion.FusionUnitsManager:
        return self.design.fusionUnitsManager
    

def get_sketch_by_name(name: str | None) -> adsk.fusion.Sketch | None:
    """Get a sketch by its name"""
    if not name:
        return None
    
    ctx = FusionContext()
    return ctx.rootComp.sketches.itemByName(name)
    
def errorHandler(func: callable) -> callable:
    """Decorator to handle Fusion 360 API errors"""
    @wraps(func)
    def wrapper(*args, **kwargs):
        try:
            return func(*args, **kwargs)
        except Exception as e:
            return f"Tool {func.__name__} error: {str(e)}"
    return wrapper


def convert_direction(direction: list[float]) -> str:
    """
    Converts a 3-element direction vector into a valid Fusion 360 expression string
    using the active design's default length unit.
    
    Args:
        direction (list[float]): A 3-element list representing the vector.
        
    Returns:
        str: A string formatted as "x unit, y unit, z unit"
    """
    GeometryValidator.validateVector(direction)
    unit = FusionContext().fusionUnitsManager.defaultLengthUnits
    return f"{direction[0]} {unit}, {direction[1]} {unit}, {direction[2]} {unit}"

class UnitsConverter:
    """Handles unit conversion between different measurement systems using static calls."""
    
    @staticmethod
    def mmToInternal(mm_value: float) -> float:
        return mm_value / 10.0
        
    @staticmethod
    def internalToMm(internal_value: float) -> float:
        return internal_value * 10.0

class GeometryValidator:
    """Validates geometry inputs for common operations"""
    
    @staticmethod
    def validatePoint(point: list[float]) -> None:
        if len(point) != 3:
            raise ValueError("Point must contain three coordinates (x, y, z)")
    
    @staticmethod
    def validateVector(vector: list[float]) -> None:
        if len(vector) != 3:
            raise ValueError("Vector must contain three components (x, y, z)")
        
