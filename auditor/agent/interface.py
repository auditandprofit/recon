from pydantic import BaseModel, Field
from typing import Any, Dict


class NLRequest(BaseModel):
    kind: str = "RETRIEVE"
    objective: str
    context: Dict[str, Any] = {}
    limits: Dict[str, Any] = {}


class NLResponse(BaseModel):
    output: str = ""
    meta: Dict[str, Any] = Field(default_factory=dict)
