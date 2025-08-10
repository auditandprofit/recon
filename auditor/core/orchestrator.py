"""Minimal orchestrator coordinating NL requests."""

import time
import dataclasses
import json
import logging
import re
from dataclasses import dataclass
from typing import Any, Awaitable, Callable, Dict, List, Optional

from auditor.agent.interface import NLRequest, NLResponse
from auditor.agent.openai import openai_generate_response
from auditor.core.models import AuditReport, Condition, Finding, Status

Json = Dict[str, Any]


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


def _messages_for(req: NLRequest) -> List[Dict[str, str]]:
    sys = (
        "You are a precise auditing assistant.\n"
        "- For RETRIEVE: decide status for the condition.\n"
        "- For DISCOVER: propose missing sub-conditions.\n"
        "Return ONLY JSON with keys: final (string), children (list of {text})."
    )
    if req.kind == "RETRIEVE":
        user = (
            f"Objective: {req.objective}\n\n"
            f"Context:\n{json.dumps(req.context, ensure_ascii=False)}\n\n"
            'Respond ONLY as JSON: {"final":"PASS: ...|FAIL: ...|maybe","children":[]}'
        )
    else:  # DISCOVER
        user = (
            f"Objective: {req.objective}\n\n"
            f"Context:\n{json.dumps(req.context, ensure_ascii=False)}\n\n"
            'Respond ONLY as JSON: {"final":"","children":[{"text":"child 1"},{"text":"child 2"}]}'
        )
    return [{"role": "system", "content": sys}, {"role": "user", "content": user}]


_json_pat = re.compile(r"\{.*\}", re.S)


def _extract_json(text: str) -> Json:
    m = _json_pat.search(text or "")
    raw = m.group(0) if m else "{}"
    try:
        data = json.loads(raw)
    except json.JSONDecodeError:
        data = {}
    final = str(data.get("final") or "").strip()
    kids = data.get("children") or []
    children = []
    for k in kids:
        t = str((k or {}).get("text", "")).strip()
        if t:
            children.append({"text": t})
    return {"final": final, "children": children}


def _call_responses(req: NLRequest) -> NLResponse:
    messages = _messages_for(req)
    rsp = openai_generate_response(messages=messages, model="o3", reasoning_effort="high")
    text = getattr(rsp, "output_text", None)
    if not text:
        parts = []
        for item in getattr(rsp, "output", []) or []:
            if getattr(item, "type", None) == "message":
                for c in getattr(item, "content", []) or []:
                    if getattr(c, "type", None) == "output_text":
                        parts.append(getattr(c, "text", ""))
        text = "".join(parts)
    data = _extract_json(text)
    logging.debug("Responses parsed → final=%r children=%d", data["final"], len(data["children"]))
    if req.kind == "RETRIEVE" and not data["final"]:
        data["final"] = "maybe"
    return NLResponse(final=data["final"], children=data["children"])


@dataclass
class Orchestrator:
    """Coordinate retrieval and discovery of conditions."""

    agent_run: Callable[[NLRequest], Awaitable[NLResponse]]
    max_depth: int = 0
    max_fanout: int = 10
    discover_on_unknown: bool = True
    on_event: Optional[Callable[[str, dict], None]] = None
    use_responses: bool = False

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
            objective=f"Validate: {cond.text}",
            context={
                "finding": _to_dict(finding),
                "condition": _to_dict(cond),
                "ancestors": [_to_dict(a) for a in ancestors],
            },
        )
        try:
            if self.use_responses:
                # res = await self.agent_run(req)   # TODO(agent)
                res = _call_responses(req)
            else:
                res = await self.agent_run(req)
        except Exception:  # pragma: no cover - agent failures
            res = NLResponse(final="")

        status = _status_from(res.final)
        cond.plan_params.update(status=status.value, final=res.final)
        self._emit(
            "node:result",
            {
                "condition": cond.text,
                "id": cond.id,
                "depth": depth,
                "status": status.value,
                "final": res.final,
                "finding_id": finding.id,
            },
        )

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
                self._emit(
                    "discover:start",
                    {"condition": cond.text, "id": cond.id, "depth": depth},
                )
                if self.use_responses:
                    # dres = await self.agent_run(dreq)  # TODO(agent)
                    dres = _call_responses(dreq)
                else:
                    dres = await self.agent_run(dreq)
                kids = dres.children
            except Exception:  # pragma: no cover - agent failures
                kids = []
            self._emit(
                "discover:result",
                {"condition": cond.text, "id": cond.id, "depth": depth, "children": kids},
            )

        for spec in (kids or [])[: self.max_fanout]:
            child = Condition(text=spec.get("text", ""), parent_id=cond.id)
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


__all__ = ["Orchestrator", "_status_from"]

