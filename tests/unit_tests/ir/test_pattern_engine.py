from __future__ import annotations

import pytest

from asdl.ir.patterns import (
    AtomizedEndpoint,
    AtomizedPattern,
    PATTERN_DUPLICATE_ATOM,
    PATTERN_EMPTY_SPLICE,
    PATTERN_UNEXPANDED,
    atomize_endpoint,
    atomize_pattern,
    expand_endpoint,
    expand_pattern,
    split_endpoint_atom,
)


def _atom(
    literal: str,
    segment_index: int,
    base_name: str,
    pattern_parts: list[str | int],
) -> AtomizedPattern:
    return AtomizedPattern(
        literal=literal,
        segment_index=segment_index,
        base_name=base_name,
        pattern_parts=pattern_parts,
    )


def _endpoint(
    inst: str,
    port: str,
    segment_index: int,
    base_name: str,
    pattern_parts: list[str | int],
) -> AtomizedEndpoint:
    return AtomizedEndpoint(
        inst=inst,
        port=port,
        segment_index=segment_index,
        base_name=base_name,
        pattern_parts=pattern_parts,
    )


def test_expand_pattern_range_ordering() -> None:
    expanded, diagnostics = expand_pattern("DATA<3:0>")

    assert diagnostics == []
    assert expanded == ["DATA3", "DATA2", "DATA1", "DATA0"]


def test_expand_pattern_left_to_right_order() -> None:
    expanded, diagnostics = expand_pattern("MN<1|2>.D<0|1>")

    assert diagnostics == []
    assert expanded == ["MN1.D0", "MN1.D1", "MN2.D0", "MN2.D1"]


def test_expand_pattern_detects_duplicate_atoms() -> None:
    expanded, diagnostics = expand_pattern("OUT<P|P>")

    assert expanded is None
    assert len(diagnostics) == 1
    assert diagnostics[0].code == PATTERN_DUPLICATE_ATOM


def test_expand_pattern_rejects_empty_splice_segment() -> None:
    expanded, diagnostics = expand_pattern("A;;B")

    assert expanded is None
    assert len(diagnostics) == 1
    assert diagnostics[0].code == PATTERN_EMPTY_SPLICE


def test_expand_pattern_rejects_splice_when_disabled() -> None:
    expanded, diagnostics = expand_pattern("OUT<P|N>;CLK", allow_splice=False)

    assert expanded is None
    assert len(diagnostics) == 1
    assert diagnostics[0].code == PATTERN_UNEXPANDED


def test_atomize_pattern_preserves_literal_parts_and_segments() -> None:
    atoms, diagnostics = atomize_pattern("OUT<P|N>;CLK<1:0>")

    assert diagnostics == []
    assert atoms == [
        _atom("OUTP", 0, "OUT", ["P"]),
        _atom("OUTN", 0, "OUT", ["N"]),
        _atom("CLK1", 1, "CLK", [1]),
        _atom("CLK0", 1, "CLK", [0]),
    ]


def test_atomize_pattern_preserves_literal_base_name() -> None:
    atoms, diagnostics = atomize_pattern("BIAS_<A|B>_X<2:1>")

    assert diagnostics == []
    assert atoms == [
        _atom("BIAS_A_X2", 0, "BIAS__X", ["A", 2]),
        _atom("BIAS_A_X1", 0, "BIAS__X", ["A", 1]),
        _atom("BIAS_B_X2", 0, "BIAS__X", ["B", 2]),
        _atom("BIAS_B_X1", 0, "BIAS__X", ["B", 1]),
    ]


def test_expand_endpoint_uses_full_expression() -> None:
    endpoints, diagnostics = expand_endpoint("MN<P|N>", "D<0|1>")

    assert diagnostics == []
    assert endpoints == [
        ("MNP", "D0"),
        ("MNP", "D1"),
        ("MNN", "D0"),
        ("MNN", "D1"),
    ]


def test_atomize_endpoint_uses_full_expression() -> None:
    endpoints, diagnostics = atomize_endpoint("MN<P|N>", "D<0|1>")

    assert diagnostics == []
    assert endpoints == [
        _endpoint("MNP", "D0", 0, "MN.D", ["P", "0"]),
        _endpoint("MNP", "D1", 0, "MN.D", ["P", "1"]),
        _endpoint("MNN", "D0", 0, "MN.D", ["N", "0"]),
        _endpoint("MNN", "D1", 0, "MN.D", ["N", "1"]),
    ]


def test_split_endpoint_atom_requires_single_dot() -> None:
    assert split_endpoint_atom("U1.D") == ("U1", "D")
    with pytest.raises(ValueError):
        split_endpoint_atom("U1")
    with pytest.raises(ValueError):
        split_endpoint_atom("U1.D.S")
