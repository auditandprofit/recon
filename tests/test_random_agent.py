import asyncio

from auditor.agent.interface import NLRequest
from auditor.agent.random_agent import RandomAgent


def test_random_agent_seed_and_bounds():
    agent_a = RandomAgent(seed=42, max_children=3)
    agent_b = RandomAgent(seed=42, max_children=3)

    async def run(agent):
        r1 = await agent.run(NLRequest(kind="RETRIEVE", objective="o"))
        r2 = await agent.run(NLRequest(kind="DISCOVER", objective="o"))
        return r1, r2

    a1, a2 = asyncio.run(run(agent_a))
    b1, b2 = asyncio.run(run(agent_b))

    choices = {"PASS: looks good", "FAIL: needs work", "maybe"}
    assert a1.evidence[0].snippet in choices
    assert a1.evidence[0].snippet == b1.evidence[0].snippet
    assert a2.evidence[0].snippet == b2.evidence[0].snippet
