"""Minimal orchestrator coordinating NL requests."""

import time
import dataclasses
from dataclasses import dataclass
from typing import Awaitable, Callable, List, Tuple

from auditor.agent.interface import NLRequest, NLResponse
from auditor.core.models import AuditReport, Condition, Finding, Status


def _status_from(text: str) -> Status:
    t = text.lower()
    if "satisf" in t or "pass" in t:
        return Status.SATISFIED
    if "violate" in t or "fail" in t:
        return Status.VIOLATED
    return Status.UNKNOWN


def _to_dict(obj):
    return dataclasses.asdict(obj)


def _conditions_without_children(f: Finding) -> List[Tuple[Condition, List[Condition]]]:
    result: List[Tuple[Condition, List[Condition]]] = []

    def visit(cond: Condition, ancestors: List[Condition]) -> None:
        if not cond.children:
            result.append((cond, ancestors))
        else:
            for child in cond.children:
                visit(child, ancestors + [cond])

    for root in f.root_conditions:
        visit(root, [])
    return result


def _walk_all_conditions(f: Finding) -> List[Tuple[Condition, List[Condition]]]:
    result: List[Tuple[Condition, List[Condition]]] = []

    def visit(cond: Condition, ancestors: List[Condition]) -> None:
        result.append((cond, ancestors))
        for child in cond.children:
            visit(child, ancestors + [cond])

    for root in f.root_conditions:
        visit(root, [])
    return result


@dataclass
class Orchestrator:
    agent_run: Callable[[NLRequest], Awaitable[NLResponse]]
    discover_depth: int = 0

    async def run(self, findings: List[Finding]) -> AuditReport:
        started = time.time()
        if self.discover_depth > 0:
            await self._discover(findings, self.discover_depth)
        await self._validate(findings)
        finished = time.time()
        return AuditReport(findings=findings, started_at=started, finished_at=finished)

    async def _discover(self, findings: List[Finding], depth: int) -> None:
        for _ in range(depth):
            for f in findings:
                for cond, ancestors in _conditions_without_children(f):
                    req = NLRequest(
                        kind="DISCOVER",
                        objective=f"Expand: {cond.text}",
                        context={
                            "finding": _to_dict(f),
                            "parent_condition": _to_dict(cond),
                            "ancestors": [_to_dict(a) for a in ancestors],
                        },
                    )
                    res: NLResponse = await self.agent_run(req)
                    for child_spec in res.children:
                        child = Condition(text=child_spec.get("text", ""), parent_id=cond.id)
                        cond.children.append(child)

    async def _validate(self, findings: List[Finding]) -> None:
        for f in findings:
            for cond, ancestors in _walk_all_conditions(f):
                req = NLRequest(
                    kind="RETRIEVE",
                    objective=f"Validate: {cond.text}",
                    context={
                        "finding": _to_dict(f),
                        "condition": _to_dict(cond),
                        "ancestors": [_to_dict(a) for a in ancestors],
                    },
                )
                res: NLResponse = await self.agent_run(req)
                status = _status_from(res.final)
                cond.plan_params["status"] = status.value
                cond.plan_params["final"] = res.final
