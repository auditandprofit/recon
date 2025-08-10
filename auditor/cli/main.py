"""Command line interface for the auditor prototype."""

import argparse
import asyncio

from auditor.agent import shell_agent
from auditor.agent.random_agent import RandomAgent
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
    parser.add_argument("--random", action="store_true", help="Use random agent")
    parser.add_argument("--seed", type=int, help="Seed for random agent")
    parser.add_argument("--findings", type=int, default=1, help="Number of initial findings")
    parser.add_argument("--no-stream", action="store_true", help="Disable live event stream")
    args = parser.parse_args()

    def printer(evt: str, data: dict) -> None:
        depth = data.get("depth", 0)
        indent = "  " * depth
        if evt == "node:start":
            print(f"{indent}- {data.get('condition', '')}", flush=True)
        elif evt == "node:result":
            status = data.get("status", "")
            final = data.get("final", "")
            print(f"{indent}  -> {status}: {final}", flush=True)
        elif evt == "discover:start":
            print(f"{indent}  ? discover", flush=True)
        elif evt == "discover:result":
            kids = data.get("children", [])
            print(f"{indent}  discovered {len(kids)}", flush=True)
        elif evt == "child:add":
            print(f"{indent}  + {data.get('condition', '')}", flush=True)

    if args.random:
        agent = RandomAgent(seed=args.seed, max_children=args.max_fanout).run
        findings = []
        for i in range(args.findings):
            f = Finding(claim=f"random-claim-{i+1}", origin_file="random")
            f.root_conditions.append(Condition(text=f"root-{i+1}"))
            findings.append(f)
        on_event = None if args.no_stream else printer
    else:
        agent = shell_agent.run
        f = Finding(claim="placeholder", origin_file="")
        f.root_conditions.append(Condition(text="stub"))
        findings = [f]
        on_event = None

    orch = Orchestrator(
        agent,
        max_depth=args.max_depth,
        max_fanout=args.max_fanout,
        discover_on_unknown=not args.no_discover_on_unknown,
        on_event=on_event,
    )

    report = asyncio.run(orch.run(findings))
    print(render_report(report))


if __name__ == "__main__":  # pragma: no cover - entry point
    main()
