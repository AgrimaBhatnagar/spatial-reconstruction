from __future__ import annotations
from dataclasses import dataclass, asdict
@dataclass
class ConfidenceInterval:
    value: float
    unit: str
    lower: float
    upper: float
    confidence_level: float = 0.95
    status: str = "provisional"
    method: str = "model_uncertainty"
def make_interval(value, unit, relative_uncertainty, *, status="provisional", method="model_uncertainty"):
    value=float(value); d=abs(value)*float(relative_uncertainty)
    return asdict(ConfidenceInterval(value,unit,max(0.0,value-d),value+d,0.95,status,method))
def measurement(name,value,unit,relative_uncertainty,*,status="provisional",method="model_uncertainty"):
    return {"name":name,"measurement":make_interval(value,unit,relative_uncertainty,status=status,method=method)}
