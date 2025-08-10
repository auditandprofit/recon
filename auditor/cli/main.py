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
    parser.add_argument("--max-depth", type=int, default=0, help="Maximum discovery depth")
    parser.add_argument(
        "--max-fanout", type=int, default=10, help="Maximum number of children per node"
    )
    parser.add_argument(
        "--no-discover-on-unknown",
        action="store_true",
        help="Disable DISCOVER calls when status is UNKNOWN",
    )
    args = parser.parse_args()

    orch = Orchestrator(
        shell_agent.run,
        max_depth=args.max_depth,
        max_fanout=args.max_fanout,
        discover_on_unknown=not args.no_discover_on_unknown,
    )

    finding = Finding(claim="placeholder", origin_file="")
    finding.root_conditions.append(Condition(text="stub"))

    report = asyncio.run(orch.run([finding]))
    print(render_report(report))


if __name__ == "__main__":  # pragma: no cover - entry point
    main()
