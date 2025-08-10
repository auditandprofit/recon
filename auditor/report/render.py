"""Helpers to render audit reports."""

from typing import List

from auditor.core.models import AuditReport


def render_report(report: AuditReport) -> str:
    lines: List[str] = ["# Audit Report"]
    for idx, finding in enumerate(report.findings, 1):
        lines.append(f"## Finding {idx}: {finding.claim}")
        lines.append(f"Origin: {finding.origin_file}")
        for cond in finding.root_conditions:
            status = cond.plan_params.get("status", "UNKNOWN")
            final = cond.plan_params.get("final", "")
            lines.append(f"- [{status}] {cond.text}")
            if final:
                lines.append(f"    → {final}")
    return "\n".join(lines) + "\n"
