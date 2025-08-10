import asyncio

from auditor.agent.interface import NLRequest, NLResponse
from auditor.core.models import Condition, Finding
import json

from auditor.core.orchestrator import Orchestrator
from auditor.report.render import render_report_text, render_report_json


async def dummy_agent(req: NLRequest) -> NLResponse:
    return NLResponse(output="PASS: looks good")


def test_orchestrator_report_includes_status_and_final():
    orch = Orchestrator(dummy_agent)
    finding = Finding(claim="claim", origin_file="orig")
    finding.root_conditions.append(Condition(text="cond"))
    report = asyncio.run(orch.run([finding]))
    cond = report.findings[0].root_conditions[0]
    assert cond.plan_params["status"] == "SATISFIED"
    assert "PASS" in cond.plan_params["final"]
    text = render_report_text(report)
    assert "[SATISFIED]" in text
    assert "PASS:" in text
    data = json.loads(render_report_json(report))
    assert data["findings"][0]["id"] == finding.id
