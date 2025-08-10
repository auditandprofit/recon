"""Example shell-based agent that counts TODO comments."""

import asyncio

from .interface import NLRequest, NLResponse


async def run(request: NLRequest) -> NLResponse:
    proc = await asyncio.create_subprocess_shell(
        r"grep -RIn 'TODO' . || true",
        stdout=asyncio.subprocess.PIPE,
        stderr=asyncio.subprocess.STDOUT,
    )
    out, _ = await proc.communicate()
    lines = out.decode("utf-8", "ignore").splitlines()
    if lines:
        return NLResponse(final=f"Found {len(lines)} TODOs.")
    return NLResponse(final="No TODOs found.")
