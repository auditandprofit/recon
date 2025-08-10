from __future__ import annotations

"""Command line interface for the auditor prototype."""

import argparse
import asyncio
from pathlib import Path

from auditor.agent import shell_agent
from auditor.core.models import Condition, Finding
from auditor.core.orchestrator import Orchestrator
from auditor.core.storage import BlobStore, EventLog
from auditor.report.render import render_report


def main() -> None:
    parser = argparse.ArgumentParser(description="Run auditor prototype")
    parser.add_argument("--repo", default=".", help="Path to repository root")
    args = parser.parse_args()

    blob_store = BlobStore(Path("blobs"))
    event_log = EventLog(Path("events.log"))
    orch = Orchestrator(blob_store, event_log, shell_agent.run)

    # For now we seed with a single dummy finding and condition.
    finding = Finding(claim="placeholder", origin_file="")
    finding.root_conditions.append(Condition(text="stub"))

    report = asyncio.run(orch.run([finding]))
    print(render_report(report))


if __name__ == "__main__":  # pragma: no cover - entry point
    main()
