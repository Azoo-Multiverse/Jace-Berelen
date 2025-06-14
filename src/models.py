from pydantic import BaseModel
from typing import Optional

class CalculationRequest(BaseModel):
    operation: str
    x: float
    y: float

    def validate_operation(self):
        valid_ops = ["add", "subtract", "multiply", "divide"]
        if self.operation not in valid_ops:
            raise ValueError(f"Operation must be one of: {valid_ops}")

class CalculationResponse(BaseModel):
    result: Optional[float] = None
    operation: str
    success: bool
    error: Optional[str] = None