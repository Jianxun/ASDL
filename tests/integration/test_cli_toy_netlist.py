"""
CLI integration test for toy example using ASDL_PATH and top module override.
"""

import sys
from pathlib import Path
import os
import subprocess
import pytest


def test_cli_toy_netlist_runs_and_emits_error_for_bad_model(tmp_path: Path):
    repo_root = Path(__file__).resolve().parents[2]
    asdl_exe = repo_root / "venv" / "bin" / "asdl"
    toy_dir = repo_root / "examples" / "imports" / "toy"
    top_asdl = toy_dir / "top.asdl"

    # Ensure the toy example is present; skip if the repo doesn't include it
    if not top_asdl.exists():
        pytest.skip("toy example not present in this checkout")

    # Invoke CLI; set ASDL_PATH to toy dir (no CLI search-path)
    env = dict(**os.environ)
    env["ASDL_PATH"] = str(toy_dir)
    proc = subprocess.run(
        [str(asdl_exe), "netlist", str(top_asdl)],
        cwd=str(repo_root),
        env=env,
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
        text=True,
    )

    # Expect non-zero exit when model name is incorrect (E0443)
    assert proc.returncode != 0
    out = proc.stdout
    assert "E0443" in out
    assert "Module Not Found in Import" in out


