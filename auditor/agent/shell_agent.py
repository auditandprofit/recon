from __future__ import annotations

"""Shell based retrieval agent."""

import asyncio
from pathlib import Path
from typing import List

from .interface import Artifact, PlanItem, RetrievalRequest, RetrievalResponse, Span
from auditor.core.storage import BlobStore


async def run(request: RetrievalRequest, blobs: BlobStore) -> RetrievalResponse:
    """Execute a retrieval request and return raw artifacts.

    The agent intentionally performs no interpretation of results.  It
    simply executes commands and reads files, returning their raw
    outputs.
    """

    repo_root = Path(request.context.get("repo_root", "."))
    spans: List[Span] = []
    artifacts: List[Artifact] = []

    for item in request.plan:
        if item.cmd:
            proc = await asyncio.create_subprocess_shell(
                item.cmd,
                cwd=repo_root,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.STDOUT,
            )
            out, _ = await proc.communicate()
            digest = blobs.put(out)
            artifacts.append(
                Artifact(kind="stdout", sha256=digest, bytes=len(out), note=item.why)
            )
        if item.read_file:
            path = repo_root / item.read_file
            text = path.read_text(encoding="utf-8")
            start = end = None
            if item.slice:
                start = item.slice.start
                end = item.slice.end
                lines = text.splitlines()
                snippet = "\n".join(lines[start - 1 : end])
            else:
                snippet = text
            spans.append(
                Span(
                    file=item.read_file,
                    start_line=start,
                    end_line=end,
                    snippet=snippet,
                )
            )

    return RetrievalResponse(spans=spans, artifacts=artifacts)
