from asdl.ast import parse_string
from asdl.ast.named_patterns import (
    AST_NAMED_PATTERN_INVALID,
    AST_NAMED_PATTERN_UNDEFINED,
    elaborate_named_patterns,
)
from asdl.diagnostics import Severity
from asdl.ir.patterns import (
    PATTERN_DUPLICATE_ATOM,
    PATTERN_EMPTY_ENUM,
    PATTERN_EMPTY_SPLICE,
    PATTERN_INVALID_RANGE,
    PATTERN_TOO_LARGE,
    PATTERN_UNEXPANDED,
    expand_pattern,
)


def test_expand_range_ordering() -> None:
    expanded, diagnostics = expand_pattern("DATA[3:0]")

    assert diagnostics == []
    assert expanded == ["DATA3", "DATA2", "DATA1", "DATA0"]


def test_expand_enum_and_splice() -> None:
    expanded, diagnostics = expand_pattern("OUT<P|N>;CLK[1:0]")

    assert diagnostics == []
    assert expanded == ["OUTP", "OUTN", "CLK1", "CLK0"]


def test_expand_left_to_right_order() -> None:
    expanded, diagnostics = expand_pattern("MN<1|2>.D<0|1>")

    assert diagnostics == []
    assert expanded == ["MN1.D0", "MN1.D1", "MN2.D0", "MN2.D1"]


def test_expand_detects_duplicate_atoms() -> None:
    expanded, diagnostics = expand_pattern("OUT<P|P>")

    assert expanded is None
    assert len(diagnostics) == 1
    diag = diagnostics[0]
    assert diag.code == PATTERN_DUPLICATE_ATOM
    assert diag.severity is Severity.ERROR


def test_expand_rejects_empty_enum() -> None:
    expanded, diagnostics = expand_pattern("OUT<|>")

    assert expanded is None
    assert len(diagnostics) == 1
    assert diagnostics[0].code == PATTERN_EMPTY_ENUM


def test_expand_rejects_empty_splice_segment() -> None:
    expanded, diagnostics = expand_pattern("A;;B")

    assert expanded is None
    assert len(diagnostics) == 1
    assert diagnostics[0].code == PATTERN_EMPTY_SPLICE


def test_expand_rejects_invalid_range() -> None:
    expanded, diagnostics = expand_pattern("BUS[3:]")

    assert expanded is None
    assert len(diagnostics) == 1
    assert diagnostics[0].code == PATTERN_INVALID_RANGE


def test_expand_rejects_unterminated_enum() -> None:
    expanded, diagnostics = expand_pattern("BUS<0|1")

    assert expanded is None
    assert len(diagnostics) == 1
    assert diagnostics[0].code == PATTERN_UNEXPANDED


def test_expand_rejects_comma_enum_delimiter() -> None:
    expanded, diagnostics = expand_pattern("MN_OUT<P,N>")

    assert expanded is None
    assert len(diagnostics) == 1
    assert diagnostics[0].code == PATTERN_UNEXPANDED


def test_expand_rejects_overflow() -> None:
    expanded, diagnostics = expand_pattern("BUS[0:10000]")

    assert expanded is None
    assert len(diagnostics) == 1
    assert diagnostics[0].code == PATTERN_TOO_LARGE


def test_named_pattern_macro_substitution() -> None:
    yaml_content = """
modules:
  top:
    patterns:
      POL: "<P|N>"
      IDX: "[1:0]"
    instances:
      U<@POL>: "res w=W<@IDX>"
    nets:
      OUT<@POL>:
        - "U<@POL>.P"
      $BUS<@IDX>:
        - "U<@POL>.P"
    instance_defaults:
      res:
        bindings:
          p: "NET<@POL>"
devices:
  res:
    backends:
      ngspice:
        template: "R{inst} {ports}"
"""
    document, parse_diags = parse_string(yaml_content)

    assert parse_diags == []
    assert document is not None

    diagnostics, had_error = elaborate_named_patterns(document)

    assert diagnostics == []
    assert had_error is False

    module = document.modules["top"]
    assert "U<P|N>" in module.instances
    assert module.instances["U<P|N>"] == "res w=W[1:0]"
    assert "OUT<P|N>" in module.nets
    assert module.nets["OUT<P|N>"] == ["U<P|N>.P"]
    assert "$BUS[1:0]" in module.nets
    assert module.nets["$BUS[1:0]"] == ["U<P|N>.P"]
    defaults = module.instance_defaults["res"]
    assert defaults.bindings["p"] == "NET<P|N>"


def test_named_pattern_invalid_definition_emits_diagnostic() -> None:
    yaml_content = """
modules:
  top:
    patterns:
      bad-name: "<0|1>"
    instances:
      U1: "res"
    nets:
      OUT:
        - "U1.P"
devices:
  res:
    backends:
      ngspice:
        template: "R{inst} {ports}"
"""
    document, parse_diags = parse_string(yaml_content)

    assert parse_diags == []
    assert document is not None

    diagnostics, had_error = elaborate_named_patterns(document)

    assert had_error is True
    assert any(diag.code == AST_NAMED_PATTERN_INVALID for diag in diagnostics)
    diag = next(diag for diag in diagnostics if diag.code == AST_NAMED_PATTERN_INVALID)
    assert diag.severity is Severity.ERROR
    assert diag.primary_span is not None


def test_named_pattern_undefined_reference_emits_diagnostic() -> None:
    yaml_content = """
modules:
  top:
    instances:
      U1: "res"
    nets:
      OUT:
        - "U1.<@MISSING>"
devices:
  res:
    backends:
      ngspice:
        template: "R{inst} {ports}"
"""
    document, parse_diags = parse_string(yaml_content)

    assert parse_diags == []
    assert document is not None

    diagnostics, had_error = elaborate_named_patterns(document)

    assert had_error is True
    assert any(diag.code == AST_NAMED_PATTERN_UNDEFINED for diag in diagnostics)
    diag = next(diag for diag in diagnostics if diag.code == AST_NAMED_PATTERN_UNDEFINED)
    assert diag.severity is Severity.ERROR
    assert diag.primary_span is not None
