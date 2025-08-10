"""Core data models for auditor."""

from dataclasses import dataclass, field
from enum import Enum
from typing import Dict, List


class Status(str, Enum):
    """Tri-state condition status used by the orchestrator."""

    UNKNOWN = "UNKNOWN"
    SATISFIED = "SATISFIED"
    VIOLATED = "VIOLATED"


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
