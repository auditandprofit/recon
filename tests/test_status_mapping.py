from auditor.core.orchestrator import _status_from
from auditor.core.models import Status


def test_status_from():
    assert _status_from("PASS: ok") is Status.SATISFIED
    assert _status_from("FAIL: nope") is Status.VIOLATED
    assert _status_from("maybe") is Status.UNKNOWN
