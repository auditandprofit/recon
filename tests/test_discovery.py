import asyncio

from auditor.agent.interface import NLRequest, NLResponse
from auditor.core.models import Condition, Finding
from auditor.core.orchestrator import Orchestrator


def test_discovery_creates_children_and_parent_context():
    requests = []

    async def agent(req: NLRequest) -> NLResponse:
        requests.append(req)
        if req.kind == "DISCOVER":
            parent_text = req.context["parent_condition"]["text"]
            return NLResponse(final="", children=[{"text": f"{parent_text}.child"}])
        return NLResponse(final="PASS: ok")

    orch = Orchestrator(agent, discover_depth=1)
    finding = Finding(claim="claim", origin_file="orig")
    finding.root_conditions.append(Condition(text="root"))

    asyncio.run(orch.run([finding]))

    root = finding.root_conditions[0]
    assert root.children and root.children[0].text == "root.child"

    child = root.children[0]
    assert child.plan_params["status"] == "SATISFIED"
    assert "PASS" in child.plan_params["final"]

    disc_req = next(r for r in requests if r.kind == "DISCOVER")
    assert disc_req.context["parent_condition"]["text"] == "root"
    assert disc_req.context["ancestors"] == []

    val_req = next(
        r
        for r in requests
        if r.kind == "RETRIEVE" and r.context["condition"]["text"] == "root.child"
    )
    assert val_req.context["ancestors"][0]["text"] == "root"


def test_discovery_depth_limit_respected():
    async def agent(req: NLRequest) -> NLResponse:
        if req.kind == "DISCOVER":
            parent_text = req.context["parent_condition"]["text"]
            if parent_text == "root":
                return NLResponse(final="", children=[{"text": "child1"}])
            if parent_text == "child1":
                return NLResponse(final="", children=[{"text": "grandchild"}])
            return NLResponse(final="", children=[])
        return NLResponse(final="PASS: ok")

    finding = Finding(claim="c", origin_file="o")
    finding.root_conditions.append(Condition(text="root"))

    orch = Orchestrator(agent, discover_depth=1)
    asyncio.run(orch.run([finding]))

    root = finding.root_conditions[0]
    assert len(root.children) == 1
    assert root.children[0].text == "child1"
    assert root.children[0].children == []
