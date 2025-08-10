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
    assert a1.output in choices
    assert a1.output == b1.output
    assert a2.output == b2.output
