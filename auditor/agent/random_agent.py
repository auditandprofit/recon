"""Pseudo-random agent for demo mode."""

from __future__ import annotations

import random
from typing import List

from .interface import NLRequest, NLResponse


class RandomAgent:
    """Agent that generates stochastic responses for testing."""

    def __init__(self, seed: int | None = None, max_children: int = 0) -> None:
        self._rng = random.Random(seed)
        self._max_children = max_children

    async def run(self, request: NLRequest) -> NLResponse:
        if request.kind == "RETRIEVE":
            outcome = self._rng.choices(
                ["PASS: looks good", "FAIL: needs work", "maybe"],
                weights=[1, 1, 3],
            )[0]
            return NLResponse(final=outcome)

        if request.kind == "DISCOVER":
            parent = request.context.get("parent_condition", {}).get("text", "")
            count = self._rng.randint(0, self._max_children)
            kids: List[dict] = [
                {"text": f"{parent} \u203a sub-{i}"} for i in range(count)
            ]
            return NLResponse(final="", children=kids)

        return NLResponse(final="maybe")


__all__ = ["RandomAgent"]
