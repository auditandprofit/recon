import asyncio

from auditor.agent.interface import NLRequest
from auditor.agent import shell_agent


def test_shell_agent_returns_output(tmp_path, monkeypatch):
    (tmp_path / "a.txt").write_text("no todos here")
    monkeypatch.chdir(tmp_path)
    req = NLRequest(objective="find todos")
    res = asyncio.run(shell_agent.run(req))
    assert res.output == ""
    (tmp_path / "b.txt").write_text("TODO one")
    res = asyncio.run(shell_agent.run(req))
    assert "b.txt:1:TODO one" in res.output
