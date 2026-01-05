from pathlib import Path

from click.testing import CliRunner

from asdl.cli import cli


def test_cli_schema_creates_files(tmp_path: Path) -> None:
    runner = CliRunner()
    result = runner.invoke(cli, ["schema", "--out", str(tmp_path)])

    assert result.exit_code == 0
    json_path = tmp_path / "schema.json"
    txt_path = tmp_path / "schema.txt"
    assert json_path.exists()
    assert txt_path.exists()
    assert json_path.stat().st_size > 0
    assert txt_path.stat().st_size > 0
