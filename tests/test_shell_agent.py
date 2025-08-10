import asyncio

from auditor.agent.interface import NLRequest
from auditor.agent import shell_agent


def test_shell_agent_returns_evidence(tmp_path, monkeypatch):
    (tmp_path / "a.txt").write_text("no todos here")
    monkeypatch.chdir(tmp_path)
    req = NLRequest(objective="find todos")
    res = asyncio.run(shell_agent.run(req))
    assert res.evidence == []
    (tmp_path / "b.txt").write_text("TODO one")
    res = asyncio.run(shell_agent.run(req))
    assert len(res.evidence) == 1
    ev = res.evidence[0]
    assert ev.path.endswith("b.txt")
    assert ev.line == 1
