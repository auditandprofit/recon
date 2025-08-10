import asyncio

from auditor.agent.interface import NLRequest, NLResponse
from auditor.core.models import Condition, Finding
from auditor.core.orchestrator import Orchestrator


def test_orchestrator_emits_events_with_depth():
    events = []

    async def agent(req: NLRequest) -> NLResponse:
        if req.kind == "DISCOVER":
            return NLResponse(final="", children=[{"text": "child"}])
        text = req.context["condition"]["text"]
        if text == "child":
            return NLResponse(final="PASS: ok")
        return NLResponse(final="maybe")

    def on_event(evt: str, data: dict) -> None:
        events.append((evt, data))

    finding = Finding(claim="c", origin_file="o")
    finding.root_conditions.append(Condition(text="root"))

    orch = Orchestrator(agent, max_depth=1, on_event=on_event)
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
    # Depth and condition propagated
    assert events[0][1]["depth"] == 0
    assert events[0][1]["condition"] == "root"
    assert events[4][1]["depth"] == 1
    assert events[4][1]["condition"] == "child"
