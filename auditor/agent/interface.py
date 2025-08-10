from pydantic import BaseModel, Field
from typing import Any, Dict, List, Optional


class NLRequest(BaseModel):
    kind: str = "RETRIEVE"
    objective: str
    context: Dict[str, Any] = {}
    limits: Dict[str, Any] = {}


class Evidence(BaseModel):
    path: str
    line: int
    snippet: str
    note: Optional[str] = None


class NLResponse(BaseModel):
    evidence: List[Evidence] = Field(default_factory=list)
