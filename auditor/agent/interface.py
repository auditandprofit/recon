from pydantic import BaseModel
from typing import Dict, Any


class NLRequest(BaseModel):
    kind: str = "RETRIEVE"
    objective: str
    context: Dict[str, Any] = {}
    limits: Dict[str, Any] = {}


class NLResponse(BaseModel):
    final: str
