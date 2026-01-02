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
            "      $VIN: MN_IN.G",
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
    assert (device_loc.start_line, device_loc.start_col) == (9, 5)


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


def test_parse_string_requires_top_with_multiple_modules() -> None:
    yaml_content = "\n".join(
        [
            "modules:",
            "  mod_a:",
            "    nets:",
            "      $A: I1.P",
            "  mod_b:",
            "    nets:",
            "      $B: I2.P",
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
            "      $VIN: MN_IN.G",
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
    assert (diag.primary_span.start.line, diag.primary_span.start.col) == (5, 5)
