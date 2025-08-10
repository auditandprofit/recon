from __future__ import annotations

"""Helpers to render audit reports."""

from typing import List
from auditor.core.models import AuditReport


def render_report(report: AuditReport) -> str:
    lines: List[str] = ["# Audit Report"]
    for idx, finding in enumerate(report.findings, 1):
        lines.append(f"## Finding {idx}: {finding.claim}")
        lines.append(f"Origin: {finding.origin_file}")
        for cond in finding.root_conditions:
            lines.append(f"- {cond.text}")
    return "\n".join(lines) + "\n"
