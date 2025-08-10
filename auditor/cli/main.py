"""Command line interface for the auditor prototype."""

import argparse
import asyncio
import os
import sys

from auditor.agent import shell_agent
from auditor.agent.random_agent import RandomAgent
from auditor.agent import llm_agent
from auditor.core.models import Condition, Finding
from auditor.core.orchestrator import Orchestrator
from auditor.report.render import _tag, render_report_json, render_report_text


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
    parser.add_argument(
        "--agent",
        choices=["shell", "llm"],
        default="shell",
        help="Which non-random agent to use",
    )
    parser.add_argument("--seed", type=int, help="Seed for random agent")
    parser.add_argument("--findings", type=int, default=1, help="Number of initial findings")
    parser.add_argument("--no-stream", action="store_true", help="Disable live event stream")
    parser.add_argument(
        "--format",
        choices=["text", "json", "json-pretty"],
        default="text",
        help="Output format for final report",
    )
    parser.add_argument(
        "--with-tags",
        action="store_true",
        help="Include ids in text report",
    )
    args = parser.parse_args()

    use_color = sys.stdout.isatty() and "NO_COLOR" not in os.environ
    ICONS = {"SATISFIED": "✔", "VIOLATED": "✖", "UNKNOWN": "?"}
    COLORS = {
        "SATISFIED": "\x1b[32m",
        "VIOLATED": "\x1b[31m",
        "UNKNOWN": "\x1b[33m",
        "RESET": "\x1b[0m",
    }

    def printer(evt: str, data: dict) -> None:
        depth = data.get("depth", 0)
        indent = "  " * (depth + 1)
        if evt == "node:start":
            if depth == 0:
                print(f"{_tag('FINDING', data.get('finding_id'))} {data.get('condition', '')}", flush=True)
        elif evt == "node:result":
            status = data.get("status", "UNKNOWN")
            final = data.get("final", "")
            icon = ICONS.get(status, "")
            status_text = status
            if use_color and status in COLORS:
                color = COLORS[status]
                icon = f"{color}{icon}{COLORS['RESET']}"
                status_text = f"{color}{status}{COLORS['RESET']}"
            print(
                f"{indent}{_tag('COND', data.get('id'))} -> {icon} {status_text}: {final}",
                flush=True,
            )
        elif evt == "discover:result":
            kids = data.get("children", [])
            print(f"{indent}[DISCOVER] discovered={len(kids)}", flush=True)
        elif evt == "child:add":
            print(
                f"{indent}{_tag('CHILD', data.get('id'))} {data.get('condition', '')}",
                flush=True,
            )

    if args.random:
        agent = RandomAgent(seed=args.seed, max_children=args.max_fanout).run
        findings = []
        for i in range(args.findings):
            f = Finding(claim=f"random-claim-{i+1}", origin_file="random")
            f.root_conditions.append(Condition(text=f"root-{i+1}"))
            findings.append(f)
        on_event = None if args.no_stream else printer
    else:
        if args.agent == "llm":
            agent = llm_agent.run
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
    if args.format == "json":
        print(render_report_json(report))
    elif args.format == "json-pretty":
        print(render_report_json(report, pretty=True))
    else:
        print(render_report_text(report, with_tags=args.with_tags))


if __name__ == "__main__":  # pragma: no cover - entry point
    main()
