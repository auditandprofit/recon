"""Shell-based agent that returns TODO comment locations."""

import asyncio

from .interface import Evidence, NLRequest, NLResponse


async def run(request: NLRequest) -> NLResponse:
    proc = await asyncio.create_subprocess_shell(
        r"grep -RIn 'TODO' . || true",
        stdout=asyncio.subprocess.PIPE,
        stderr=asyncio.subprocess.STDOUT,
    )
    out, _ = await proc.communicate()
    lines = out.decode("utf-8", "ignore").splitlines()
    evidence = []
    for line in lines:
        try:
            path, lineno, snippet = line.split(":", 2)
            evidence.append(Evidence(path=path, line=int(lineno), snippet=snippet.strip()))
        except ValueError:
            continue
    return NLResponse(evidence=evidence)
