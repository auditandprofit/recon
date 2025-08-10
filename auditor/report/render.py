"""Helpers to render audit reports."""

import dataclasses
import json
from typing import List

from auditor.core.models import AuditReport


def _tag(prefix: str, identifier: str) -> str:
    """Return a bracketed tag for ``identifier``."""
    return f"[{prefix}:{identifier}]"


def render_report_text(report: AuditReport, with_tags: bool = False) -> str:
    """Render a human readable audit report."""
    lines: List[str] = ["# Audit Report"]
    for idx, finding in enumerate(report.findings, 1):
        tag = f"{_tag('FINDING', finding.id)} " if with_tags else ""
        lines.append(f"## {tag}Finding {idx}: {finding.claim}")
        lines.append(f"Origin: {finding.origin_file}")
        for cond in finding.root_conditions:
            status = cond.plan_params.get("status", "UNKNOWN")
            final = cond.plan_params.get("final", "")
            ctag = f"{_tag('COND', cond.id)} " if with_tags else ""
            lines.append(f"- {ctag}[{status}] {cond.text}")
            if final:
                lines.append(f"    → {final}")
    return "\n".join(lines) + "\n"


def render_report_json(report: AuditReport, pretty: bool = False) -> str:
    """Render ``AuditReport`` as JSON."""
    data = dataclasses.asdict(report)
    data["duration"] = report.finished_at - report.started_at
    if pretty:
        return json.dumps(data, indent=2)
    return json.dumps(data)


__all__ = ["render_report_text", "render_report_json", "_tag"]
