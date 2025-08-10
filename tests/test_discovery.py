import asyncio
from typing import List

from auditor.agent.interface import NLRequest, NLResponse
from auditor.core.models import Condition, Finding
from auditor.core.orchestrator import Orchestrator


def test_depth_zero_no_children():
    requests = []

    async def agent(req: NLRequest) -> NLResponse:
        requests.append(req)
        return NLResponse()

    finding = Finding(claim="c", origin_file="o")
    finding.root_conditions.append(Condition(text="root"))

    orch = Orchestrator(agent, max_depth=0, discover_fn=lambda c, o: ["child"])
    asyncio.run(orch.run([finding]))

    root = finding.root_conditions[0]
    assert root.children == []
    assert all(r.kind == "RETRIEVE" for r in requests)


def test_unknown_triggers_discover_until_depth():
    requests = []

    async def agent(req: NLRequest) -> NLResponse:
        requests.append(req)
        return NLResponse()

    def discover_fn(cond: Condition, output: str) -> List[str]:
        if cond.text == "root":
            return ["child"]
        if cond.text == "child":
            return ["grand"]
        return []

    finding = Finding(claim="c", origin_file="o")
    finding.root_conditions.append(Condition(text="root"))

    orch = Orchestrator(agent, max_depth=2, discover_fn=discover_fn)
    asyncio.run(orch.run([finding]))

    root = finding.root_conditions[0]
    assert [c.text for c in root.children] == ["child"]
    child = root.children[0]
    assert [c.text for c in child.children] == ["grand"]
    assert child.children[0].children == []
    assert all(r.kind == "RETRIEVE" for r in requests)


def test_fanout_cap_enforced():
    async def agent(req: NLRequest) -> NLResponse:
        return NLResponse()

    def discover_fn(cond: Condition, output: str) -> List[str]:
        return [f"child{i}" for i in range(5)]

    finding = Finding(claim="c", origin_file="o")
    finding.root_conditions.append(Condition(text="root"))

    orch = Orchestrator(agent, max_depth=1, max_fanout=2, discover_fn=discover_fn)
    asyncio.run(orch.run([finding]))

    root = finding.root_conditions[0]
    assert len(root.children) == 2


def test_no_discover_when_status_known():
    requests = []

    async def agent(req: NLRequest) -> NLResponse:
        requests.append(req)
        if req.context["condition"]["text"] == "root":
            return NLResponse(output="PASS: ok")
        return NLResponse()

    def discover_fn(cond: Condition, output: str) -> List[str]:
        return ["child"]

    finding = Finding(claim="c", origin_file="o")
    finding.root_conditions.append(Condition(text="root"))

    orch = Orchestrator(agent, max_depth=1, discover_fn=discover_fn)
    asyncio.run(orch.run([finding]))

    root = finding.root_conditions[0]
    assert root.children == []
    assert len(requests) == 1


def test_no_discover_when_disabled():
    requests = []

    async def agent(req: NLRequest) -> NLResponse:
        requests.append(req)
        return NLResponse()

    def discover_fn(cond: Condition, output: str) -> List[str]:
        return ["child"]

    finding = Finding(claim="c", origin_file="o")
    finding.root_conditions.append(Condition(text="root"))

    orch = Orchestrator(
        agent, max_depth=1, discover_on_unknown=False, discover_fn=discover_fn
    )
    asyncio.run(orch.run([finding]))

    root = finding.root_conditions[0]
    assert root.children == []
    assert all(r.kind == "RETRIEVE" for r in requests)

