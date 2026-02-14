from __future__ import annotations

from pathlib import Path

from asdl.tools.completion.engine import CompletionEngine


def _write(path: Path, content: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(content, encoding="utf-8")


def test_engine_completes_endpoints_import_symbols_and_params(tmp_path: Path) -> None:
    workspace = tmp_path / "ws"
    workspace.mkdir()

    _write(
        workspace / ".asdlrc",
        "\n".join(
            [
                "schema_version: 1",
                "lib_roots:",
                "  - libs",
            ]
        )
        + "\n",
    )

    _write(
        workspace / "libs" / "analog.asdl",
        "\n".join(
            [
                "devices:",
                "  fet:",
                "    ports: [D, G, S, B]",
                "    parameters:",
                "      l: 1u",
                "      w: 2u",
                "    backends:",
                "      ngspice:",
                "        template: \"M{inst} {D} {G} {S} {B} {model}\"",
                "modules:",
                "  child:",
                "    nets:",
                "      $IN:",
                "        - X1.P",
            ]
        )
        + "\n",
    )

    entry_text = "\n".join(
        [
            "imports:",
            "  lib: analog.asdl",
            "modules:",
            "  top:",
            "    instances:",
            "      M1: lib.fet l=1u ",
            "    nets:",
            "      $OUT:",
            "        - M1.",
        ]
    ) + "\n"
    entry_file = workspace / "top.asdl"
    _write(entry_file, entry_text)

    engine = CompletionEngine()
    engine.initialize(workspace_roots=[workspace])
    engine.update_document(uri=entry_file.as_uri(), version=1, text=entry_text)

    import_items = engine.complete(
        uri=entry_file.as_uri(),
        line=5,
        character=len("      M1: lib"),
    )
    assert any(item.insert_text == "lib.fet" for item in import_items)

    param_items = engine.complete(
        uri=entry_file.as_uri(),
        line=5,
        character=len("      M1: lib.fet l=1u "),
    )
    assert any(item.insert_text == "l=" for item in param_items)
    assert any(item.insert_text == "w=" for item in param_items)

    endpoint_items = engine.complete(
        uri=entry_file.as_uri(),
        line=8,
        character=len("        - M1."),
    )
    assert any(item.insert_text == "M1.D" for item in endpoint_items)
    assert any(item.insert_text == "M1.G" for item in endpoint_items)


def test_engine_uses_updated_document_text_for_context(tmp_path: Path) -> None:
    entry_file = tmp_path / "top.asdl"
    original = "\n".join(
        [
            "modules:",
            "  top:",
            "    instances:",
            "      M1: dev",
        ]
    ) + "\n"
    updated = "\n".join(
        [
            "modules:",
            "  top:",
            "    instances:",
            "      M1: dev ",
        ]
    ) + "\n"
    _write(entry_file, original)

    engine = CompletionEngine()
    engine.update_document(uri=entry_file.as_uri(), version=1, text=updated)

    items = engine.complete(
        uri=entry_file.as_uri(),
        line=3,
        character=len("      M1: dev "),
    )
    assert isinstance(items, list)
