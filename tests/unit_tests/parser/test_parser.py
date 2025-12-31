from asdl.ast import parse_string
from asdl.diagnostics import Severity


def _basic_yaml(*, include_port_order: bool = True, port_dir: str = "in") -> str:
    lines = [
        "modules:",
        "  my_mod:",
        "    ports:",
        "      a:",
        f"        dir: {port_dir}",
    ]
    if include_port_order:
        lines.append("    port_order: [a]")
    lines.extend(
        [
            "    views:",
            "      nominal:",
            "        kind: subckt",
        ]
    )
    return "\n".join(lines)


def test_parse_string_success_attaches_locations() -> None:
    yaml_content = _basic_yaml()

    document, diagnostics = parse_string(yaml_content)

    assert diagnostics == []
    assert document is not None

    module_loc = document.modules["my_mod"]._loc
    assert module_loc is not None
    assert (module_loc.start_line, module_loc.start_col) == (3, 5)

    port_loc = document.modules["my_mod"].ports["a"]._loc
    assert port_loc is not None
    assert (port_loc.start_line, port_loc.start_col) == (5, 9)


def test_parse_string_invalid_root_type() -> None:
    document, diagnostics = parse_string("- item")

    assert document is None
    assert len(diagnostics) == 1
    diag = diagnostics[0]
    assert diag.code == "PARSE-002"
    assert diag.severity is Severity.ERROR
    assert diag.primary_span is not None
    assert (diag.primary_span.start.line, diag.primary_span.start.col) == (1, 1)


def test_parse_string_missing_required_field_location() -> None:
    yaml_content = _basic_yaml(include_port_order=False)

    document, diagnostics = parse_string(yaml_content)

    assert document is None
    assert diagnostics
    diag = diagnostics[0]
    assert diag.code == "PARSE-003"
    assert "port_order" in diag.message
    assert diag.primary_span is not None
    assert (diag.primary_span.start.line, diag.primary_span.start.col) == (3, 5)


def test_parse_string_invalid_enum_location() -> None:
    yaml_content = _basic_yaml(port_dir="sideways")

    document, diagnostics = parse_string(yaml_content)

    assert document is None
    assert diagnostics
    diag = diagnostics[0]
    assert diag.code == "PARSE-003"
    assert diag.primary_span is not None
    assert (diag.primary_span.start.line, diag.primary_span.start.col) == (5, 14)
