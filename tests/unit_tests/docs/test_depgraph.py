import hashlib
from pathlib import Path

from asdl.docs.depgraph import (
    UNRESOLVED_DEVICE_REFERENCE,
    UNRESOLVED_UNKNOWN_SYMBOL,
    build_dependency_graph,
    dependency_graph_to_jsonable,
)


def _hash_file_id(file_id: str) -> str:
    return hashlib.sha1(file_id.encode("utf-8")).hexdigest()[:8]


def _module_id(name: str, file_id: str) -> str:
    return f"{name}__{_hash_file_id(file_id)}"


def test_depgraph_build_and_edges(tmp_path: Path) -> None:
    lib_path = tmp_path / "lib.asdl"
    entry_path = tmp_path / "entry.asdl"

    lib_path.write_text("modules:\n  Child: {}\n", encoding="utf-8")
    entry_path.write_text(
        "imports:\n"
        "  lib: ./lib.asdl\n"
        "top: Top\n"
        "modules:\n"
        "  Top:\n"
        "    instances:\n"
        "      u_lib: \"lib.Child\"\n"
        "      u_local: \"Local\"\n"
        "      u_device: \"Res\"\n"
        "      u_missing: \"lib.Missing\"\n"
        "  Local: {}\n"
        "devices:\n"
        "  Res:\n"
        "    backends:\n"
        "      sim.ngspice:\n"
        "        template: \"R {ports}\"\n",
        encoding="utf-8",
    )

    graph, diagnostics = build_dependency_graph([entry_path])
    assert diagnostics == []
    assert graph is not None

    payload = dependency_graph_to_jsonable(graph)
    assert payload["schema_version"] == 1
    assert set(payload.keys()) == {
        "schema_version",
        "files",
        "modules",
        "instances",
        "edges",
        "unresolved",
    }

    entry_id = str(entry_path.absolute())
    lib_id = str(lib_path.absolute())
    expected_files = sorted(
        [
            {"file_id": entry_id, "entry": True},
            {"file_id": lib_id, "entry": False},
        ],
        key=lambda item: item["file_id"],
    )
    assert payload["files"] == expected_files

    top_id = _module_id("Top", entry_id)
    local_id = _module_id("Local", entry_id)
    child_id = _module_id("Child", lib_id)

    modules_by_id = {module["module_id"]: module for module in payload["modules"]}
    assert modules_by_id[top_id]["name"] == "Top"
    assert modules_by_id[top_id]["file_id"] == entry_id
    assert modules_by_id[local_id]["name"] == "Local"
    assert modules_by_id[child_id]["name"] == "Child"

    instances_by_id = {inst["instance_id"]: inst for inst in payload["instances"]}
    assert instances_by_id[f"{top_id}:u_lib"]["ref"] == "lib.Child"
    assert instances_by_id[f"{top_id}:u_local"]["ref"] == "Local"
    assert instances_by_id[f"{top_id}:u_device"]["ref"] == "Res"
    assert instances_by_id[f"{top_id}:u_missing"]["ref"] == "lib.Missing"

    edges = {
        (edge["from_module_id"], edge["to_module_id"], edge["instance_id"])
        for edge in payload["edges"]
    }
    assert edges == {
        (top_id, child_id, f"{top_id}:u_lib"),
        (top_id, local_id, f"{top_id}:u_local"),
    }

    unresolved = {item["instance_id"]: item for item in payload["unresolved"]}
    assert unresolved[f"{top_id}:u_device"]["reason"] == UNRESOLVED_DEVICE_REFERENCE
    assert unresolved[f"{top_id}:u_missing"]["reason"] == UNRESOLVED_UNKNOWN_SYMBOL


def test_depgraph_accepts_inline_quoted_and_structured_instances(tmp_path: Path) -> None:
    entry_path = tmp_path / "entry.asdl"
    entry_path.write_text(
        "top: top\n"
        "modules:\n"
        "  child: {}\n"
        "  top:\n"
        "    instances:\n"
        "      x_inline: \"child cmd='.TRAN 0 10u' mode=tran\"\n"
        "      x_struct:\n"
        "        ref: child\n"
        "        parameters:\n"
        "          cmd: \".TRAN 0 10u\"\n"
        "          mode: tran\n"
        "devices:\n"
        "  code:\n"
        "    ports: [P]\n"
        "    backends:\n"
        "      sim.ngspice:\n"
        "        template: \"X {ports}\"\n",
        encoding="utf-8",
    )

    graph, diagnostics = build_dependency_graph([entry_path])
    assert diagnostics == []
    assert graph is not None

    payload = dependency_graph_to_jsonable(graph)
    entry_id = str(entry_path.absolute())
    top_id = _module_id("top", entry_id)
    child_id = _module_id("child", entry_id)

    instances_by_id = {inst["instance_id"]: inst for inst in payload["instances"]}
    assert instances_by_id[f"{top_id}:x_inline"]["ref"] == "child"
    assert instances_by_id[f"{top_id}:x_struct"]["ref"] == "child"

    edge_targets = {
        edge["instance_id"]: edge["to_module_id"] for edge in payload["edges"]
    }
    assert edge_targets[f"{top_id}:x_inline"] == child_id
    assert edge_targets[f"{top_id}:x_struct"] == child_id
