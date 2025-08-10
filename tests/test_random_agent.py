import asyncio

from auditor.agent.interface import NLRequest
from auditor.agent.random_agent import RandomAgent


def test_random_agent_seed_and_bounds():
    agent_a = RandomAgent(seed=42, max_children=3)
    agent_b = RandomAgent(seed=42, max_children=3)

    async def run(agent):
        r1 = await agent.run(NLRequest(kind="RETRIEVE", objective="o"))
        r2 = await agent.run(
            NLRequest(
                kind="DISCOVER",
                objective="o",
                context={"parent_condition": {"text": "root"}},
            )
        )
        return r1, r2

    a1, a2 = asyncio.run(run(agent_a))
    b1, b2 = asyncio.run(run(agent_b))

    assert a1.final in {"PASS: looks good", "FAIL: needs work", "maybe"}
    assert a1.final == b1.final
    assert a2.children == b2.children
    assert len(a2.children) <= 3
