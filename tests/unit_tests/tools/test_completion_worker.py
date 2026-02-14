from __future__ import annotations

import json
from pathlib import Path
import subprocess
import sys


WORKER_PATH = Path("extensions/asdl-language-tools/python/worker.py")


def _rpc(proc: subprocess.Popen[str], payload: dict) -> dict:
    assert proc.stdin is not None
    assert proc.stdout is not None
    proc.stdin.write(json.dumps(payload) + "\n")
    proc.stdin.flush()
    raw = proc.stdout.readline()
    assert raw
    return json.loads(raw)


def _write(path: Path, content: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(content, encoding="utf-8")


def test_worker_lifecycle_and_completion(tmp_path: Path) -> None:
    workspace = tmp_path / "ws"
    workspace.mkdir()

    _write(
        workspace / "top.asdl",
        "\n".join(
            [
                "devices:",
                "  dev:",
                "    ports: [P, N]",
                "    parameters:",
                "      l: 1u",
                "    backends:",
                "      ngspice:",
                "        template: \"X{inst} {P} {N}\"",
                "modules:",
                "  top:",
                "    instances:",
                "      X1: dev l=1u ",
            ]
        )
        + "\n",
    )

    proc = subprocess.Popen(
        [sys.executable, str(WORKER_PATH)],
        stdin=subprocess.PIPE,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        text=True,
    )
    try:
        file_uri = (workspace / "top.asdl").as_uri()
        source = (workspace / "top.asdl").read_text(encoding="utf-8")

        init_resp = _rpc(
            proc,
            {
                "id": 1,
                "method": "initialize",
                "params": {"workspace_roots": [str(workspace)]},
            },
        )
        assert init_resp["id"] == 1
        assert init_resp["ok"] is True

        update_resp = _rpc(
            proc,
            {
                "id": 2,
                "method": "update_document",
                "params": {
                    "uri": file_uri,
                    "version": 1,
                    "text": source,
                },
            },
        )
        assert update_resp["id"] == 2
        assert update_resp["ok"] is True

        complete_resp = _rpc(
            proc,
            {
                "id": 3,
                "method": "complete",
                "params": {
                    "uri": file_uri,
                    "line": 11,
                    "character": len("      X1: dev l=1u "),
                },
            },
        )
        assert complete_resp["id"] == 3
        assert complete_resp["ok"] is True
        items = complete_resp["result"]["items"]
        assert any(item["insert_text"] == "l=" for item in items)

        shutdown_resp = _rpc(
            proc,
            {
                "id": 4,
                "method": "shutdown",
                "params": {},
            },
        )
        assert shutdown_resp["id"] == 4
        assert shutdown_resp["ok"] is True
    finally:
        proc.wait(timeout=5)
