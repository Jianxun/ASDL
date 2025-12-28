from pathlib import Path

from click.testing import CliRunner

from asdl.cli import cli as asdl_cli
from asdl.ir import register_asdl_dialect


def test_ir_dump_smoke(tmp_path: Path) -> None:
    fixture = Path(__file__).resolve().parents[2] / "fixtures" / "ir" / "prim_with_ports.yml"
    runner = CliRunner()
    result = runner.invoke(asdl_cli, ["ir-dump", "--verify", str(fixture)])
    assert result.exit_code == 0, result.output
    out = result.output
    assert "asdl.module_set" in out
    assert "module @prim" in out
    # Basic sanity: ports show up in output
    assert "%port a" in out and "%port b" in out and "%port c" in out


def test_ir_dump_smoke_xdsl_engine(tmp_path: Path) -> None:
    if register_asdl_dialect is None:
        return  # skip if xDSL not installed
    fixture = Path(__file__).resolve().parents[2] / "fixtures" / "ir" / "prim_with_ports.yml"
    runner = CliRunner()
    result = runner.invoke(asdl_cli, ["ir-dump", "--verify", "--engine", "xdsl", str(fixture)])
    # If xdsl is available, we expect a success and some module text
    assert result.exit_code == 0, result.output
    out = result.output
    assert "module" in out


def test_ir_dump_lower_netlist(tmp_path: Path) -> None:
    if register_asdl_dialect is None:
        return  # skip if xDSL not installed
    fixture = Path(__file__).resolve().parents[2] / "fixtures" / "ir" / "single_inst.yml"
    runner = CliRunner()
    result = runner.invoke(
        asdl_cli,
        [
            "ir-dump",
            "--verify",
            "--engine",
            "xdsl",
            "--lower",
            "netlist",
            str(fixture),
        ],
    )
    assert result.exit_code == 0, result.output
    out = result.output
    assert "netlist.module" in out
    assert "netlist.instance" in out

