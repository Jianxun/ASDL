"""Long-lived JSON-over-stdio completion worker for ASDL language tools."""

from __future__ import annotations

import json
import sys
from typing import Any

from asdl.tools.completion.engine import CompletionEngine


def _error_payload(message: str) -> dict[str, str]:
    return {"code": "WORKER-001", "message": message}


def _write_response(payload: dict[str, Any]) -> None:
    sys.stdout.write(json.dumps(payload) + "\n")
    sys.stdout.flush()


def _handle_request(engine: CompletionEngine, request: dict[str, Any]) -> tuple[bool, dict[str, Any]]:
    request_id = request.get("id")
    method = request.get("method")
    params = request.get("params") or {}

    try:
        if method == "initialize":
            result = engine.initialize(
                workspace_roots=params.get("workspace_roots"),
                lib_roots=params.get("lib_roots"),
                config_path=params.get("config_path"),
            )
            return False, {"id": request_id, "ok": True, "result": result}

        if method == "update_document":
            result = engine.update_document(
                uri=params["uri"],
                version=int(params.get("version", 0)),
                text=params["text"],
            )
            return False, {"id": request_id, "ok": True, "result": result}

        if method == "complete":
            items = engine.complete(
                uri=params["uri"],
                line=int(params["line"]),
                character=int(params["character"]),
            )
            result = {"items": [item.to_dict() for item in items]}
            return False, {"id": request_id, "ok": True, "result": result}

        if method == "shutdown":
            result = engine.shutdown()
            return True, {"id": request_id, "ok": True, "result": result}

        return False, {"id": request_id, "ok": False, "error": _error_payload(f"Unknown method: {method}")}
    except Exception as exc:
        return False, {"id": request_id, "ok": False, "error": _error_payload(str(exc))}


def main() -> int:
    """Run the worker request loop until shutdown or EOF."""
    engine = CompletionEngine()
    should_exit = False

    for raw in sys.stdin:
        text = raw.strip()
        if not text:
            continue
        try:
            request = json.loads(text)
        except json.JSONDecodeError as exc:
            _write_response({"id": None, "ok": False, "error": _error_payload(f"Invalid JSON: {exc}")})
            continue

        should_exit, response = _handle_request(engine, request)
        _write_response(response)
        if should_exit:
            return 0

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
