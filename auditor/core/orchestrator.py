"""Minimal orchestrator coordinating NL requests."""

import dataclasses
import time
from dataclasses import dataclass
from typing import Awaitable, Callable, Dict, List, Optional

from auditor.agent.interface import NLRequest, NLResponse
from auditor.core.models import AuditReport, Condition, Finding, Status


def _status_from_output(output: str) -> Status:
    """Derive a ``Status`` from agent output."""

    text = output.lower()
    if not text:
        return Status.UNKNOWN
    if "satisf" in text or "pass" in text:
        return Status.SATISFIED
    if "violate" in text or "fail" in text:
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
    on_event: Optional[Callable[[str, dict], None]] = None
    discover_fn: Optional[Callable[[Condition, str], List[str]]] = None

    def _emit(self, evt: str, data: dict) -> None:
        if self.on_event:
            self.on_event(evt, data)

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
        self._emit(
            "node:start",
            {
                "condition": cond.text,
                "id": cond.id,
                "depth": depth,
                "finding_id": finding.id,
            },
        )
        req = NLRequest(
            kind="RETRIEVE",
            objective=f"Fetch evidence for: {cond.text}",
            context={
                "finding": _to_dict(finding),
                "condition": _to_dict(cond),
                "ancestors": [_to_dict(a) for a in ancestors],
            },
        )
        try:
            res = await self.agent_run(req)
        except Exception:  # pragma: no cover - agent failures
            res = NLResponse()

        status = _status_from_output(res.output)
        cond.plan_params.update(
            status=status.value,
            final=res.output,
            retrieval_meta=res.meta,
        )
        self._emit(
            "node:result",
            {
                "condition": cond.text,
                "id": cond.id,
                "depth": depth,
                "status": status.value,
                "final": res.output,
                "retrieval_meta": res.meta,
                "finding_id": finding.id,
            },
        )

        if status != Status.UNKNOWN or depth >= self.max_depth:
            return

        kids_text: List[str] = []
        if self.discover_on_unknown:
            self._emit(
                "discover:start",
                {"condition": cond.text, "id": cond.id, "depth": depth},
            )
            if self.discover_fn:
                kids_text = self.discover_fn(cond, res.output)
            self._emit(
                "discover:result",
                {
                    "condition": cond.text,
                    "id": cond.id,
                    "depth": depth,
                    "children": kids_text,
                },
            )

        for text in (kids_text or [])[: self.max_fanout]:
            child = Condition(text=text, parent_id=cond.id)
            cond.children.append(child)
            self._emit(
                "child:add",
                {
                    "condition": child.text,
                    "id": child.id,
                    "parent_id": cond.id,
                    "depth": depth + 1,
                },
            )
            await self._eval_node(finding, child, ancestors + [cond], depth + 1)


__all__ = ["Orchestrator", "_status_from_output"]

