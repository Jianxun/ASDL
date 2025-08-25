"""
CLI integration test for toy example with search-path and top module override.
"""

import sys
from pathlib import Path
import subprocess


def test_cli_toy_netlist_runs_and_emits_error_for_bad_model(tmp_path: Path):
    repo_root = Path(__file__).resolve().parents[2]
    asdl_exe = repo_root / "venv" / "bin" / "asdl"
    toy_dir = repo_root / "examples" / "imports" / "toy"
    top_asdl = toy_dir / "top.asdl"

    # Ensure the toy example is present
    assert top_asdl.exists()

    # Invoke CLI; do not pass --top (uses file's top) and use toy dir as search path
    proc = subprocess.run(
        [str(asdl_exe), "netlist", str(top_asdl), "--search-path", str(toy_dir)],
        cwd=str(repo_root),
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
        text=True,
    )

    # Expect non-zero exit when model name is incorrect (E0443)
    assert proc.returncode != 0
    out = proc.stdout
    assert "E0443" in out
    assert "Module Not Found in Import" in out


