from asdl.ast import parse_string
from asdl.diagnostics import Severity


def _basic_yaml(*, include_ref: bool = True, instance_name: str = "M1") -> str:
    if include_ref:
        lines = [
            "modules:",
            "  my_mod:",
            "    instances:",
            f"      {instance_name}:",
            "        ref: my_dev",
            "    nets:",
            "      $VIN:",
            f"        - inst: {instance_name}",
            "          pin: G",
        ]
    else:
        lines = [
            "modules:",
            "  my_mod:",
            "    instances:",
            f"      {instance_name}: {{}}",
            "    nets:",
            "      $VIN:",
            f"        - inst: {instance_name}",
            "          pin: G",
        ]
    return "\n".join(lines)


def test_parse_string_success_attaches_locations() -> None:
    yaml_content = _basic_yaml()

    document, diagnostics = parse_string(yaml_content)

    assert diagnostics == []
    assert document is not None

    module_loc = document.modules["my_mod"]._loc
    assert module_loc is not None
    assert (module_loc.start_line, module_loc.start_col) == (3, 5)

    instance_loc = document.modules["my_mod"].instances["M1"]._loc
    assert instance_loc is not None
    assert (instance_loc.start_line, instance_loc.start_col) == (5, 9)

    endpoint_loc = document.modules["my_mod"].nets["$VIN"][0]._loc
    assert endpoint_loc is not None
    assert (endpoint_loc.start_line, endpoint_loc.start_col) == (8, 11)


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
    yaml_content = _basic_yaml(include_ref=False)

    document, diagnostics = parse_string(yaml_content)

    assert document is None
    assert diagnostics
    diag = diagnostics[0]
    assert diag.code == "PARSE-003"
    assert "ref" in diag.message
    assert diag.primary_span is not None
    assert (diag.primary_span.start.line, diag.primary_span.start.col) == (4, 11)


def test_parse_string_invalid_name_location() -> None:
    yaml_content = "\n".join(
        [
            "modules:",
            "  my_mod:",
            "    instances:",
            "      M1:",
            "        ref: my_dev",
            "    nets:",
            "      VSS*:",
            "        - inst: M1",
            "          pin: S",
        ]
    )

    document, diagnostics = parse_string(yaml_content)

    assert document is None
    assert diagnostics
    diag = diagnostics[0]
    assert diag.code == "PARSE-003"
    assert diag.primary_span is not None
    assert (diag.primary_span.start.line, diag.primary_span.start.col) == (7, 7)
