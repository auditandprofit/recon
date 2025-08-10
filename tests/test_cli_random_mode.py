import pathlib
import subprocess
import sys

ROOT = pathlib.Path(__file__).resolve().parents[1]


def run_cli(args):
    cmd = [sys.executable, "main.py"] + args
    return subprocess.check_output(cmd, cwd=ROOT, text=True)


def test_cli_default_runs():
    out = run_cli(["--max-depth", "0", "--no-discover-on-unknown"])
    assert "# Audit Report" in out


def test_cli_random_seed_repeatable():
    args = [
        "--random",
        "--findings",
        "1",
        "--max-depth",
        "0",
        "--no-stream",
        "--seed",
        "123",
    ]
    out1 = run_cli(args)
    out2 = run_cli(args)
    assert out1 == out2
    assert out1.startswith("# Audit Report")
