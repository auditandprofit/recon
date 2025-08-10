from auditor.agent.interface import Evidence
from auditor.core.orchestrator import _status_from_evidence
from auditor.core.models import Status


def test_status_from_evidence():
    assert _status_from_evidence([Evidence(path="", line=1, snippet="PASS: ok")]) is Status.SATISFIED
    assert _status_from_evidence([Evidence(path="", line=1, snippet="FAIL: nope")]) is Status.VIOLATED
    assert _status_from_evidence([]) is Status.UNKNOWN
