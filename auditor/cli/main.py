"""Command line interface for the auditor prototype."""

import argparse
import asyncio

from auditor.agent import shell_agent
from auditor.core.models import Condition, Finding
from auditor.core.orchestrator import Orchestrator
from auditor.report.render import render_report


def main() -> None:
    parser = argparse.ArgumentParser(description="Run auditor prototype")
    parser.add_argument("--repo", default=".", help="Path to repository root")
    parser.parse_args()

    orch = Orchestrator(shell_agent.run)

    finding = Finding(claim="placeholder", origin_file="")
    finding.root_conditions.append(Condition(text="stub"))

    report = asyncio.run(orch.run([finding]))
    print(render_report(report))


if __name__ == "__main__":  # pragma: no cover - entry point
    main()
