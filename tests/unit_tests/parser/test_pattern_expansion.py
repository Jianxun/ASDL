from asdl.diagnostics import Severity
from asdl.patterns import (
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
    assert expanded == ["DATA_3", "DATA_2", "DATA_1", "DATA_0"]


def test_expand_enum_and_splice() -> None:
    expanded, diagnostics = expand_pattern("OUT<P|N>;CLK[1:0]")

    assert diagnostics == []
    assert expanded == ["OUT_P", "OUT_N", "CLK_1", "CLK_0"]


def test_expand_left_to_right_order() -> None:
    expanded, diagnostics = expand_pattern("MN<1|2>.D<0|1>")

    assert diagnostics == []
    assert expanded == ["MN_1.D_0", "MN_1.D_1", "MN_2.D_0", "MN_2.D_1"]


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


def test_expand_rejects_overflow() -> None:
    expanded, diagnostics = expand_pattern("BUS[0:10000]")

    assert expanded is None
    assert len(diagnostics) == 1
    assert diagnostics[0].code == PATTERN_TOO_LARGE
