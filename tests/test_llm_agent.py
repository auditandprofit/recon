import asyncio

from auditor.agent.interface import NLRequest, NLResponse
from auditor.core.models import Condition, Finding
from auditor.core.orchestrator import Orchestrator


async def structured_agent(req: NLRequest) -> NLResponse:
    structured = {
        "status": "UNKNOWN",
        "final": "need more evidence",
        "children": ["sub1", "sub2"],
        "next_tasks": [{"kind": "RETRIEVE", "objective": "check details"}],
        "notes": ""
    }
    # Ensure limits are passed through
    assert "max_depth_remaining" in req.limits
    assert "max_fanout" in req.limits
    return NLResponse(output="ignored", meta={"structured": structured})


def test_orchestrator_uses_structured_fields():
    finding = Finding(claim="claim", origin_file="orig")
    finding.root_conditions.append(Condition(text="root"))
    orch = Orchestrator(structured_agent, max_depth=1)
    asyncio.run(orch.run([finding]))
    root = finding.root_conditions[0]
    assert root.plan_params["status"] == "UNKNOWN"
    assert root.plan_params["final"] == "need more evidence"
    assert root.plan_params["next_tasks"] == [{"kind": "RETRIEVE", "objective": "check details"}]
    assert [c.text for c in root.children] == ["sub1", "sub2"]
