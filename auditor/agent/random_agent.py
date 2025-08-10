"""Pseudo-random agent for demo mode."""

from __future__ import annotations

import random

from .interface import Evidence, NLRequest, NLResponse


class RandomAgent:
    """Agent that generates stochastic responses for testing."""

    def __init__(self, seed: int | None = None, max_children: int = 0) -> None:
        self._rng = random.Random(seed)
        self._max_children = max_children

    async def run(self, request: NLRequest) -> NLResponse:
        snippet = self._rng.choices(
            ["PASS: looks good", "FAIL: needs work", "maybe"],
            weights=[1, 1, 3],
        )[0]
        ev = Evidence(path="random.txt", line=1, snippet=snippet)
        return NLResponse(evidence=[ev])


__all__ = ["RandomAgent"]
