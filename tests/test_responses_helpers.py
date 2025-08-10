from auditor.core.orchestrator import _extract_json, _status_from


def test_extract_json_accepts_wrapped_text():
    text = "Sure.\n{\"final\":\"PASS: ok\",\"children\":[{\"text\":\"child\"}]}\nThanks!"
    out = _extract_json(text)
    assert out["final"].startswith("PASS")
    assert out["children"] == [{"text": "child"}]


def test_status_mapping_unchanged():
    assert _status_from("PASS: yep").value == "SATISFIED"
    assert _status_from("FAIL: nope").value == "VIOLATED"
    assert _status_from("maybe").value == "UNKNOWN"

