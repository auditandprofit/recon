"""Minimal orchestrator coordinating NL requests."""

import time
import dataclasses
from dataclasses import dataclass
from typing import Awaitable, Callable, List

from auditor.agent.interface import NLRequest, NLResponse
from auditor.core.models import AuditReport, Condition, Finding, Status


def _status_from(text: str) -> Status:
    """Map natural language response text to a ``Status``."""

    t = (text or "").strip().lower()
    if "satisf" in t or "pass" in t:
        return Status.SATISFIED
    if "violate" in t or "fail" in t:
        return Status.VIOLATED
    return Status.UNKNOWN


def _to_dict(obj):
    return dataclasses.asdict(obj)


@dataclass
class Orchestrator:
    """Coordinate retrieval and discovery of conditions."""

    agent_run: Callable[[NLRequest], Awaitable[NLResponse]]
    max_depth: int = 0
    max_fanout: int = 10
    discover_on_unknown: bool = True

    async def run(self, findings: List[Finding]) -> AuditReport:
        started = time.time()
        for f in findings:
            for root in f.root_conditions:
                await self._eval_node(f, root, [], 0)
        finished = time.time()
        return AuditReport(findings=findings, started_at=started, finished_at=finished)

    async def _eval_node(
        self, finding: Finding, cond: Condition, ancestors: List[Condition], depth: int
    ) -> None:
        req = NLRequest(
            kind="RETRIEVE",
            objective=f"Validate: {cond.text}",
            context={
                "finding": _to_dict(finding),
                "condition": _to_dict(cond),
                "ancestors": [_to_dict(a) for a in ancestors],
            },
        )
        try:
            res = await self.agent_run(req)
        except Exception:  # pragma: no cover - agent failures
            res = NLResponse(final="")

        status = _status_from(res.final)
        cond.plan_params.update(status=status.value, final=res.final)

        if status != Status.UNKNOWN or depth >= self.max_depth:
            return

        kids = res.children
        if not kids and self.discover_on_unknown:
            dreq = NLRequest(
                kind="DISCOVER",
                objective=f"Expand: {cond.text}",
                context={
                    "finding": _to_dict(finding),
                    "parent_condition": _to_dict(cond),
                    "ancestors": [_to_dict(a) for a in ancestors],
                },
            )
            try:
                dres = await self.agent_run(dreq)
                kids = dres.children
            except Exception:  # pragma: no cover - agent failures
                kids = []

        for spec in (kids or [])[: self.max_fanout]:
            child = Condition(text=spec.get("text", ""), parent_id=cond.id)
            cond.children.append(child)
            await self._eval_node(finding, child, ancestors + [cond], depth + 1)


__all__ = ["Orchestrator", "_status_from"]

