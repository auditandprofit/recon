from auditor.core.orchestrator import _status_from_output
from auditor.core.models import Status


def test_status_from_output():
    assert _status_from_output("PASS: ok") is Status.SATISFIED
    assert _status_from_output("FAIL: nope") is Status.VIOLATED
    assert _status_from_output("") is Status.UNKNOWN
