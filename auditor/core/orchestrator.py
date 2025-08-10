from __future__ import annotations

"""Minimal orchestrator coordinating retrieval tasks."""

import asyncio
import time
from dataclasses import dataclass
from typing import Awaitable, Callable, Deque, List, Tuple
from collections import deque

from auditor.core.models import AuditReport, Condition, Evidence, Finding, Status
from auditor.core.storage import BlobStore, EventLog
from auditor.agent.interface import PlanItem, RetrievalRequest, RetrievalResponse


@dataclass
class Orchestrator:
    blob_store: BlobStore
    events: EventLog
    agent_run: Callable[[RetrievalRequest, BlobStore], Awaitable[RetrievalResponse]]
    max_depth: int = 1
    max_children: int = 0

    async def run(self, findings: List[Finding]) -> AuditReport:
        started = time.time()
        queue: Deque[Tuple[Finding, Condition, int, List[str]]] = deque()
        for f in findings:
            for idx, cond in enumerate(f.root_conditions):
                queue.append((f, cond, 0, [f"root[{idx}]"]))
                self.events.emit(
                    "TASK_ENQUEUED", {"finding": f.claim, "path": [f"root[{idx}]"], "depth": 0}
                )

        while queue:
            finding, cond, depth, path = queue.popleft()
            plan = self.make_plan(finding, cond, depth)
            req = RetrievalRequest(
                objective="Collect evidence for condition",
                context={
                    "repo_root": ".",
                    "finding": finding.__dict__,
                    "condition": cond.__dict__,
                    "depth": depth,
                },
                plan=plan,
                limits={},
            )
            self.events.emit("TASK_STARTED", {"path": path, "depth": depth})
            res = await self.agent_run(req, self.blob_store)
            evidence = self.evidence_from(res)
            status, children = self.decide(cond, evidence)
            self.events.emit(
                "NODE_STATUS",
                {
                    "path": path,
                    "status": status.value,
                },
            )
            self.events.emit("TASK_FINISHED", {"path": path})
            if depth + 1 <= self.max_depth:
                for i, child in enumerate(children[: self.max_children]):
                    queue.append((finding, child, depth + 1, path + [f"child[{i}]"]))
                    self.events.emit(
                        "TASK_ENQUEUED",
                        {
                            "path": path + [f"child[{i}]"]
                        },
                    )

        finished = time.time()
        return AuditReport(findings=findings, started_at=started, finished_at=finished, meta={})

    # --- helpers -------------------------------------------------------
    def make_plan(self, finding: Finding, condition: Condition, depth: int) -> List[PlanItem]:
        return []

    def evidence_from(self, res: RetrievalResponse) -> Evidence:
        return Evidence(summary="", locations=[], artifacts=[])

    def decide(self, cond: Condition, evidence: Evidence) -> Tuple[Status, List[Condition]]:
        return Status.UNKNOWN, []
