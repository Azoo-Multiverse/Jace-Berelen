---
task_id: calc_api
agent: developer
type: implementation
dependencies: ["calc_api_strategist"]
status: ready
---

# Development Task

Based on strategist analysis, implement the following:

## 1. Create src/models.py
```python
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
```

## 2. Create src/operations.py
```python
def calculate(operation: str, x: float, y: float) -> float:
    if operation == "add":
        return x + y
    elif operation == "subtract":
        return x - y
    elif operation == "multiply":
        return x * y
    elif operation == "divide":
        if y == 0:
            raise ValueError("Division by zero")
        return x / y
    else:
        raise ValueError(f"Unknown operation: {operation}")
```

## 3. Create src/app.py
```python
from fastapi import FastAPI, HTTPException
from .models import CalculationRequest, CalculationResponse
from .operations import calculate

app = FastAPI(title="Calculator API")

@app.post("/calculate", response_model=CalculationResponse)
async def perform_calculation(request: CalculationRequest):
    try:
        request.validate_operation()
        result = calculate(request.operation, request.x, request.y)
        return CalculationResponse(
            result=result,
            operation=request.operation,
            success=True
        )
    except ValueError as e:
        return CalculationResponse(
            operation=request.operation,
            success=False,
            error=str(e)
        )
```

## 4. Create tests/test_operations.py
```python
import pytest
from src.operations import calculate

def test_addition():
    assert calculate("add", 2, 3) == 5

def test_subtraction():
    assert calculate("subtract", 5, 3) == 2

def test_multiplication():
    assert calculate("multiply", 4, 3) == 12

def test_division():
    assert calculate("divide", 10, 2) == 5

def test_division_by_zero():
    with pytest.raises(ValueError):
        calculate("divide", 1, 0)

def test_invalid_operation():
    with pytest.raises(ValueError):
        calculate("power", 2, 3)
```

## 5. Create tests/test_api.py
```python
from fastapi.testclient import TestClient
from src.app import app

client = TestClient(app)

def test_successful_calculation():
    response = client.post("/calculate", json={
        "operation": "add",
        "x": 5,
        "y": 3
    })
    assert response.status_code == 200
    data = response.json()
    assert data["success"] == True
    assert data["result"] == 8

def test_division_by_zero():
    response = client.post("/calculate", json={
        "operation": "divide",
        "x": 1,
        "y": 0
    })
    assert response.status_code == 200
    data = response.json()
    assert data["success"] == False
    assert "zero" in data["error"].lower()

def test_invalid_operation():
    response = client.post("/calculate", json={
        "operation": "power",
        "x": 2,
        "y": 3
    })
    assert response.status_code == 200
    data = response.json()
    assert data["success"] == False
    assert "operation" in data["error"].lower()
```

Implementation tasks complete. Ready for review.