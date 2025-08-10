"""Minimal orchestrator coordinating NL requests."""

import time
from dataclasses import dataclass
from typing import Awaitable, Callable, List

from auditor.agent.interface import NLRequest, NLResponse
from auditor.core.models import AuditReport, Finding, Status


def _status_from(text: str) -> Status:
    t = text.lower()
    if "satisf" in t or "pass" in t:
        return Status.SATISFIED
    if "violate" in t or "fail" in t:
        return Status.VIOLATED
    return Status.UNKNOWN


@dataclass
class Orchestrator:
    agent_run: Callable[[NLRequest], Awaitable[NLResponse]]

    async def run(self, findings: List[Finding]) -> AuditReport:
        started = time.time()
        for f in findings:
            for cond in f.root_conditions:
                req = NLRequest(
                    objective=f"Validate: {cond.text}",
                    context={"finding": f.__dict__, "condition": cond.__dict__},
                )
                res: NLResponse = await self.agent_run(req)
                status = _status_from(res.final)
                cond.plan_params["status"] = status.value
                cond.plan_params["final"] = res.final
        finished = time.time()
        return AuditReport(findings=findings, started_at=started, finished_at=finished)
