import asyncio

from auditor.agent.interface import NLRequest, NLResponse
from auditor.core.models import Condition, Finding
from auditor.core.orchestrator import Orchestrator


def test_depth_zero_no_children():
    requests = []

    async def agent(req: NLRequest) -> NLResponse:
        requests.append(req)
        return NLResponse(final="maybe")

    finding = Finding(claim="c", origin_file="o")
    finding.root_conditions.append(Condition(text="root"))

    orch = Orchestrator(agent, max_depth=0)
    asyncio.run(orch.run([finding]))

    root = finding.root_conditions[0]
    assert root.children == []
    assert all(r.kind == "RETRIEVE" for r in requests)


def test_unknown_triggers_discover_until_depth():
    requests = []

    async def agent(req: NLRequest) -> NLResponse:
        requests.append(req)
        if req.kind == "DISCOVER":
            parent = req.context["parent_condition"]["text"]
            if parent == "root":
                return NLResponse(final="", children=[{"text": "child"}])
            if parent == "child":
                return NLResponse(final="", children=[{"text": "grand"}])
            return NLResponse(final="", children=[])
        text = req.context["condition"]["text"]
        if text == "grand":
            return NLResponse(final="PASS: done")
        return NLResponse(final="maybe")

    finding = Finding(claim="c", origin_file="o")
    finding.root_conditions.append(Condition(text="root"))

    orch = Orchestrator(agent, max_depth=2)
    asyncio.run(orch.run([finding]))

    root = finding.root_conditions[0]
    assert [c.text for c in root.children] == ["child"]
    child = root.children[0]
    assert [c.text for c in child.children] == ["grand"]
    assert child.children[0].children == []
    assert sum(1 for r in requests if r.kind == "DISCOVER") == 2


def test_fanout_cap_enforced():
    async def agent(req: NLRequest) -> NLResponse:
        if req.kind == "DISCOVER":
            return NLResponse(
                final="",
                children=[{ "text": f"child{i}" } for i in range(5)],
            )
        return NLResponse(final="maybe")

    finding = Finding(claim="c", origin_file="o")
    finding.root_conditions.append(Condition(text="root"))

    orch = Orchestrator(agent, max_depth=1, max_fanout=2)
    asyncio.run(orch.run([finding]))

    root = finding.root_conditions[0]
    assert len(root.children) == 2


def test_retrieve_children_respected_without_discover():
    requests = []

    async def agent(req: NLRequest) -> NLResponse:
        requests.append(req)
        if req.kind == "RETRIEVE" and req.context["condition"]["text"] == "root":
            return NLResponse(final="maybe", children=[{"text": "child"}])
        return NLResponse(final="PASS: ok")

    finding = Finding(claim="c", origin_file="o")
    finding.root_conditions.append(Condition(text="root"))

    orch = Orchestrator(agent, max_depth=1)
    asyncio.run(orch.run([finding]))

    root = finding.root_conditions[0]
    assert [c.text for c in root.children] == ["child"]
    assert sum(1 for r in requests if r.kind == "DISCOVER") == 0


def test_no_discover_when_disabled():
    requests = []

    async def agent(req: NLRequest) -> NLResponse:
        requests.append(req)
        return NLResponse(final="maybe")

    finding = Finding(claim="c", origin_file="o")
    finding.root_conditions.append(Condition(text="root"))

    orch = Orchestrator(agent, max_depth=1, discover_on_unknown=False)
    asyncio.run(orch.run([finding]))

    root = finding.root_conditions[0]
    assert root.children == []
    assert sum(1 for r in requests if r.kind == "DISCOVER") == 0

