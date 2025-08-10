from __future__ import annotations

"""Request/response models exchanged between the orchestrator and agent."""

from typing import List, Optional
from pydantic import BaseModel, Field


class Slice(BaseModel):
    start: int
    end: int


class PlanItem(BaseModel):
    why: Optional[str] = None
    cmd: Optional[str] = None
    read_file: Optional[str] = None
    slice: Optional[Slice] = None


class RetrievalRequest(BaseModel):
    kind: str = "RETRIEVE"
    objective: str
    context: dict
    plan: List[PlanItem]
    limits: dict


class Span(BaseModel):
    file: str
    start_line: Optional[int] = None
    end_line: Optional[int] = None
    snippet: Optional[str] = None


class Artifact(BaseModel):
    kind: str
    sha256: str
    bytes: int
    note: Optional[str] = None


class RetrievalResponse(BaseModel):
    result_type: str = "RETRIEVAL_RESULT"
    spans: List[Span] = Field(default_factory=list)
    artifacts: List[Artifact] = Field(default_factory=list)
    notes: List[str] = Field(default_factory=list)
