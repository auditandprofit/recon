from __future__ import annotations

"""Core data models for auditor.

These dataclasses implement the minimal schema described in the
architectural notes.  They intentionally avoid behaviour in order to
keep them easy to serialize and reason about.
"""

from dataclasses import dataclass, field
from enum import Enum
from typing import Dict, List, Optional


class Status(str, Enum):
    """Tri-state condition status used by the orchestrator."""

    UNKNOWN = "UNKNOWN"
    SATISFIED = "SATISFIED"
    VIOLATED = "VIOLATED"


@dataclass
class CodeSpan:
    """Reference to a region of code in a file."""

    file: str
    start_line: Optional[int] = None
    end_line: Optional[int] = None
    symbol: Optional[str] = None
    snippet: Optional[str] = None


@dataclass
class ArtifactRef:
    """Reference to a stored artifact in the blob store."""

    kind: str
    sha256: str
    bytes: int
    note: Optional[str] = None


@dataclass
class Evidence:
    """Evidence collected by the retrieval agent."""

    summary: str
    locations: List[CodeSpan] = field(default_factory=list)
    artifacts: List[ArtifactRef] = field(default_factory=list)
    source: str = "agent://retrieval"


@dataclass
class Condition:
    """Condition that needs to be validated for a finding."""

    text: str
    plan_params: Dict[str, object] = field(default_factory=dict)


@dataclass
class Finding:
    """Top level finding derived from a seed file."""

    claim: str
    origin_file: str
    root_conditions: List[Condition] = field(default_factory=list)


@dataclass
class AuditReport:
    """Final report emitted by the orchestrator."""

    findings: List[Finding]
    started_at: float
    finished_at: float
    meta: Dict[str, object] = field(default_factory=dict)
