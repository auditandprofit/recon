from __future__ import annotations

from auditor.agent.interface import NLRequest, NLResponse
from auditor.agent.openai import openai_generate_response
import json
import re

SYSTEM_PROMPT = """
You are the Audit Orchestrator.
Responsibilities:
1) JUDGMENT: Decide if the condition is SATISFIED, VIOLATED, or UNKNOWN.
2) TASKS: Propose concrete retrieval tasks ("next_tasks") that would best reduce uncertainty.
3) CHILDREN: Propose optional child conditions that decompose the condition if UNKNOWN or if finer validation helps.
Output STRICT JSON exactly matching the provided schema. No extra text.
Rules:
- status ∈ {SATISFIED, VIOLATED, UNKNOWN}
- Keep final concise, evidence-focused.
- Prefer 0 children when status ≠ UNKNOWN.
"""

USER_TEMPLATE = """
Finding:
{finding}

Condition:
{text}

Ancestors (shallow summaries ok):
{ancestors}

Schema:
{schema}
"""

SCHEMA_JSON = {
    "status": "SATISFIED|VIOLATED|UNKNOWN",
    "final": "string",
    "children": ["string"],
    "next_tasks": [{"kind": "RETRIEVE", "objective": "string"}],
    "notes": "string",
}

JSON_RE = re.compile(r"\{.*\}", re.S)  # naive top-level JSON capture


async def run(req: NLRequest) -> NLResponse:
    ctx = req.context
    finding = ctx.get("finding", {})
    cond = ctx.get("condition", {})
    ancestors = ctx.get("ancestors", [])

    messages = [
        {"role": "system", "content": SYSTEM_PROMPT},
        {
            "role": "user",
            "content": USER_TEMPLATE.format(
                finding=finding,
                text=cond.get("text", ""),
                ancestors=ancestors,
                schema=json.dumps(SCHEMA_JSON, ensure_ascii=False),
            ),
        },
    ]

    resp = openai_generate_response(
        messages=messages,
        model="o3",
        reasoning_effort="high",
        temperature=0.2,
    )

    raw = str(resp)
    try:
        text = resp.output_text
    except Exception:
        text = raw

    m = JSON_RE.search(text or "")
    structured = {}
    if m:
        try:
            structured = json.loads(m.group(0))
        except Exception:
            structured = {}
    status = structured.get("status") or "UNKNOWN"
    final = structured.get("final") or ""

    return NLResponse(
        output=json.dumps(structured) if structured else text,
        meta={"structured": structured, "raw": raw},
    )

__all__ = ["run"]
