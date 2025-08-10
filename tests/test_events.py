import asyncio

from auditor.agent.interface import NLRequest, NLResponse
from auditor.core.models import Condition, Finding
from auditor.core.orchestrator import Orchestrator


def test_orchestrator_emits_events_with_depth():
    events = []

    async def agent(req: NLRequest) -> NLResponse:
        text = req.context["condition"]["text"]
        if text == "child":
            return NLResponse(output="PASS: ok")
        return NLResponse()

    def on_event(evt: str, data: dict) -> None:
        events.append((evt, data))

    finding = Finding(claim="c", origin_file="o")
    finding.root_conditions.append(Condition(text="root"))

    discover_fn = lambda c, o: ["child"] if c.text == "root" else []
    orch = Orchestrator(agent, max_depth=1, on_event=on_event, discover_fn=discover_fn)
    asyncio.run(orch.run([finding]))

    names = [e[0] for e in events]
    assert names == [
        "node:start",
        "node:result",
        "discover:start",
        "discover:result",
        "child:add",
        "node:start",
        "node:result",
    ]
    # Depth, condition, and ids propagated
    first = events[0][1]
    child_evt = events[4][1]
    assert first["depth"] == 0
    assert first["condition"] == "root"
    assert "id" in first and "finding_id" in first
    assert child_evt["depth"] == 1
    assert child_evt["condition"] == "child"
    assert "id" in child_evt and child_evt["parent_id"]
