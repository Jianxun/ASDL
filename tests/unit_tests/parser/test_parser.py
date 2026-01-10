from asdl.ast import parse_string
from asdl.diagnostics import Severity


def _basic_yaml() -> str:
    return "\n".join(
        [
            "modules:",
            "  my_mod:",
            "    instances:",
            "      MN_IN: nfet_3p3 m=8",
            "    nets:",
            "      $VIN:",
            "        - MN_IN.G",
            "devices:",
            "  nfet_3p3:",
            "    ports: [D, G, S]",
            "    backends:",
            "      ngspice:",
            "        template: \"M{inst} {D} {G} {S} {model}\"",
            "        model: nfet",
        ]
    )


def test_parse_string_success_attaches_locations() -> None:
    yaml_content = _basic_yaml()

    document, diagnostics = parse_string(yaml_content)

    assert diagnostics == []
    assert document is not None

    module_loc = document.modules["my_mod"]._loc
    assert module_loc is not None
    assert (module_loc.start_line, module_loc.start_col) == (3, 5)

    device_loc = document.devices["nfet_3p3"]._loc
    assert device_loc is not None
    assert (device_loc.start_line, device_loc.start_col) == (10, 5)


def test_parse_string_preserves_pattern_tokens() -> None:
    yaml_content = "\n".join(
        [
            "modules:",
            "  top:",
            "    instances:",
            "      \"MN<1|2>\": nfet",
            "    nets:",
            "      \"$OUT<P|N>\":",
            "        - \"MN<1|2>.D<0|1>\"",
            "      \"BUS[3:0];BUS<4|5>\":",
            "        - \"MN<1|2>.S\"",
        ]
    )

    document, diagnostics = parse_string(yaml_content)

    assert diagnostics == []
    assert document is not None
    module = document.modules["top"]
    assert "MN<1|2>" in module.instances
    assert module.instances["MN<1|2>"] == "nfet"
    assert "$OUT<P|N>" in module.nets
    assert module.nets["$OUT<P|N>"] == ["MN<1|2>.D<0|1>"]
    assert "BUS[3:0];BUS<4|5>" in module.nets
    assert module.nets["BUS[3:0];BUS<4|5>"] == ["MN<1|2>.S"]


def test_parse_string_accepts_patterns_and_instance_defaults() -> None:
    yaml_content = "\n".join(
        [
            "modules:",
            "  top:",
            "    patterns:",
            "      k: \"<1|2>\"",
            "    instance_defaults:",
            "      mos:",
            "        bindings:",
            "          B: $VSS",
            "    nets:",
            "      $OUT:",
            "        - I1.P",
        ]
    )

    document, diagnostics = parse_string(yaml_content)

    assert diagnostics == []
    assert document is not None
    module = document.modules["top"]
    assert module.patterns == {"k": "<1|2>"}
    assert module.instance_defaults["mos"].bindings == {"B": "$VSS"}


def test_parse_string_accepts_imports() -> None:
    yaml_content = "\n".join(
        [
            "imports:",
            "  gf: libs/gf.asdl",
            "modules:",
            "  top:",
            "    nets:",
            "      $OUT:",
            "        - I1.P",
        ]
    )

    document, diagnostics = parse_string(yaml_content)

    assert diagnostics == []
    assert document is not None
    assert document.imports == {"gf": "libs/gf.asdl"}


def test_parse_string_rejects_invalid_import_namespace() -> None:
    yaml_content = "\n".join(
        [
            "imports:",
            "  \"1bad\": libs/gf.asdl",
            "modules:",
            "  top: {}",
        ]
    )

    document, diagnostics = parse_string(yaml_content)

    assert document is None
    assert diagnostics
    diag = diagnostics[0]
    assert diag.code == "AST-011"
    assert diag.severity is Severity.ERROR
    assert "namespace" in diag.message


def test_parse_string_rejects_duplicate_import_namespaces() -> None:
    yaml_content = "\n".join(
        [
            "imports:",
            "  gf: libs/gf.asdl",
            "  gf: other/gf.asdl",
            "modules:",
            "  top: {}",
        ]
    )

    document, diagnostics = parse_string(yaml_content)

    assert document is None
    assert diagnostics
    diag = diagnostics[0]
    assert diag.code == "AST-013"
    assert diag.severity is Severity.ERROR


def test_parse_string_rejects_non_string_import_path() -> None:
    yaml_content = "\n".join(
        [
            "imports:",
            "  gf:",
            "    - libs/gf.asdl",
            "modules:",
            "  top: {}",
        ]
    )

    document, diagnostics = parse_string(yaml_content)

    assert document is None
    assert diagnostics
    diag = diagnostics[0]
    assert diag.code == "AST-011"
    assert diag.severity is Severity.ERROR
    assert "path" in diag.message


def test_parse_string_rejects_top_level_patterns() -> None:
    yaml_content = "\n".join(
        [
            "patterns:",
            "  k: \"<1|2>\"",
            "modules:",
            "  top:",
            "    nets:",
            "      $OUT:",
            "        - I1.P",
        ]
    )

    document, diagnostics = parse_string(yaml_content)

    assert document is None
    assert diagnostics
    diag = diagnostics[0]
    assert diag.code == "PARSE-003"
    assert "patterns" in diag.message


def test_parse_string_rejects_invalid_pattern_group() -> None:
    yaml_content = "\n".join(
        [
            "modules:",
            "  top:",
            "    patterns:",
            "      k: \"MN<1|2>\"",
            "    nets:",
            "      $OUT:",
            "        - I1.P",
        ]
    )

    document, diagnostics = parse_string(yaml_content)

    assert document is None
    assert diagnostics
    diag = diagnostics[0]
    assert diag.code == "PARSE-003"
    assert "group token" in diag.message


def test_parse_string_rejects_instance_defaults_missing_bindings() -> None:
    yaml_content = "\n".join(
        [
            "modules:",
            "  top:",
            "    instance_defaults:",
            "      mos: {}",
            "    nets:",
            "      $OUT:",
            "        - I1.P",
        ]
    )

    document, diagnostics = parse_string(yaml_content)

    assert document is None
    assert diagnostics
    diag = diagnostics[0]
    assert diag.code == "PARSE-003"
    assert "bindings" in diag.message


def test_parse_string_invalid_root_type() -> None:
    document, diagnostics = parse_string("- item")

    assert document is None
    assert len(diagnostics) == 1
    diag = diagnostics[0]
    assert diag.code == "PARSE-002"
    assert diag.severity is Severity.ERROR
    assert diag.primary_span is not None
    assert (diag.primary_span.start.line, diag.primary_span.start.col) == (1, 1)


def test_parse_string_requires_modules_or_devices() -> None:
    document, diagnostics = parse_string("top: main")

    assert document is None
    assert diagnostics
    diag = diagnostics[0]
    assert diag.code == "PARSE-003"
    assert "modules" in diag.message
    assert "devices" in diag.message


def test_parse_string_rejects_import_only_document() -> None:
    document, diagnostics = parse_string("imports:\n  gf: libs/gf.asdl")

    assert document is None
    assert diagnostics
    diag = diagnostics[0]
    assert diag.code == "PARSE-003"
    assert "modules" in diag.message
    assert "devices" in diag.message


def test_parse_string_requires_top_with_multiple_modules() -> None:
    yaml_content = "\n".join(
        [
            "modules:",
            "  mod_a:",
            "    nets:",
            "      $A:",
            "        - I1.P",
            "  mod_b:",
            "    nets:",
            "      $B:",
            "        - I2.P",
        ]
    )

    document, diagnostics = parse_string(yaml_content)

    assert document is None
    assert diagnostics
    diag = diagnostics[0]
    assert diag.code == "PARSE-003"
    assert "top" in diag.message


def test_parse_string_forbids_exports_in_module() -> None:
    yaml_content = "\n".join(
        [
            "modules:",
            "  my_mod:",
            "    nets:",
            "      $VIN:",
            "        - MN_IN.G",
            "    exports:",
            "      VIN: $VIN",
        ]
    )

    document, diagnostics = parse_string(yaml_content)

    assert document is None
    assert diagnostics
    diag = diagnostics[0]
    assert diag.code == "PARSE-003"
    assert diag.primary_span is not None
    assert (diag.primary_span.start.line, diag.primary_span.start.col) == (6, 5)


def test_parse_string_rejects_endpoint_string() -> None:
    yaml_content = "\n".join(
        [
            "modules:",
            "  my_mod:",
            "    nets:",
            "      $VIN: MN_IN.G",
        ]
    )

    document, diagnostics = parse_string(yaml_content)

    assert document is None
    assert diagnostics
    diag = diagnostics[0]
    assert diag.code == "PARSE-003"
    assert "Endpoint lists must be YAML lists" in diag.message
    assert diag.notes is not None
    assert "Endpoint lists must be YAML lists of '<instance>.<pin>' strings" in diag.notes


def test_parse_string_invalid_instance_expr_includes_hint() -> None:
    yaml_content = "\n".join(
        [
            "modules:",
            "  my_mod:",
            "    instances:",
            "      M1: 123",
        ]
    )

    document, diagnostics = parse_string(yaml_content)

    assert document is None
    assert diagnostics
    diag = diagnostics[0]
    assert diag.code == "PARSE-003"
    assert diag.notes is not None
    assert "Instance expressions use '<model> key=value ...' format" in diag.notes
