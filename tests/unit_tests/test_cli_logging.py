from pathlib import Path
import json

from click.testing import CliRunner

from asdl.cli import cli as asdl_cli


def test_cli_log_json_and_file(tmp_path: Path):
    runner = CliRunner()
    log_file = tmp_path / "cli.jsonl"
    # Invoke harmless subcommand to avoid missing-command error
    result = runner.invoke(asdl_cli, ["--debug", "--log-json", "--log-file", str(log_file), "version"])
    assert result.exit_code == 0

    # The file should have JSON logs including our initialization debug
    contents = log_file.read_text(encoding="utf-8").strip().splitlines()
    assert contents, "log file should not be empty"
    # Validate JSON structure on last line
    last = json.loads(contents[-1])
    assert "timestamp" in last
    assert last["level"] in {"DEBUG", "INFO", "TRACE", "WARNING", "ERROR"}
    assert last["component"] in {"cli", "cli"}
    assert isinstance(last["message"], str)


