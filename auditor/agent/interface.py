from pydantic import BaseModel, Field
from typing import Any, Dict, List


class NLRequest(BaseModel):
    kind: str = "RETRIEVE"
    objective: str
    context: Dict[str, Any] = {}
    limits: Dict[str, Any] = {}


class NLResponse(BaseModel):
    final: str
    children: List[Dict[str, Any]] = Field(default_factory=list)
